extends Control
var world: DawnreefWorld
var panorama: Camera3D
var gateway: Control
var card: VBoxContainer
var status_label: Label
var email: LineEdit
var password: LineEdit
var display_name: LineEdit
var server_url := "https://game.surveyroute.work/api/v1"
var busy := false
var session: PlaySession
var selected_character: Dictionary = {}

func _ready() -> void:
    GameData.load_bundle()
    theme = TideUI.theme()
    ApiClient.request_failed.connect(_request_failed)
    world = preload("res://scenes/world/dawnreef.tscn").instantiate()
    add_child(world)
    panorama = Camera3D.new()
    world.add_child(panorama)
    panorama.position = Vector3(21,14,26)
    panorama.look_at(Vector3(-1,1,-4))
    panorama.fov = 55
    panorama.current = true
    var config = ConfigFile.new()
    config.load("user://settings.cfg")
    server_url = config.get_value("network","server",server_url)
    Engine.max_fps = config.get_value("graphics","fps",30)
    world.sun.shadow_enabled = config.get_value("graphics","shadows",false)
    get_viewport().scaling_3d_scale = config.get_value("graphics","scale",.75)
    _build_gateway()
    show_login()
    if OS.has_feature("debug"):
        print("VT_GATEWAY_READY")
    if "--preview" in OS.get_cmdline_user_args():
        start_preview()

func _build_gateway() -> void:
    gateway = Control.new()
    gateway.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(gateway)
    var shade = ColorRect.new()
    shade.color = Color(.025,.08,.12,.35)
    shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    gateway.add_child(shade)
    var margin = MarginContainer.new()
    margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    for side in ["left","right","top","bottom"]:
        margin.add_theme_constant_override("margin_"+side,42)
    gateway.add_child(margin)
    var row = HBoxContainer.new()
    row.add_theme_constant_override("separation",42)
    margin.add_child(row)
    var title_column = VBoxContainer.new()
    title_column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    title_column.size_flags_vertical = Control.SIZE_SHRINK_CENTER
    row.add_child(title_column)
    title_column.add_child(TideUI.label("A WORLD ABOVE THE GLIMMERDEEP",16,TideUI.GOLD))
    title_column.add_child(TideUI.label("VEILBOUND\nTIDES",62))
    title_column.add_child(TideUI.paragraph("Follow the light.\nDiscover what answers beneath it.",25))
    var air = Control.new()
    air.custom_minimum_size.y = 36
    title_column.add_child(air)
    title_column.add_child(TideUI.paragraph("DAWNREEF ATOLL\nSpell lessons · 0.2.2",16))
    var panel = PanelContainer.new()
    panel.custom_minimum_size.x = 460
    panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
    row.add_child(panel)
    var scroll = ScrollContainer.new()
    scroll.custom_minimum_size = Vector2(428,550)
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    panel.add_child(scroll)
    card = VBoxContainer.new()
    card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    scroll.add_child(card)

func clear_card(title: String) -> void:
    for child in card.get_children():
        card.remove_child(child)
        child.queue_free()
    card.add_child(TideUI.label(title,30))

func add_status(words := "") -> void:
    status_label = TideUI.paragraph(words,16)
    card.add_child(status_label)

func show_login() -> void:
    clear_card("Your journey begins")
    card.add_child(TideUI.paragraph("Sign in to save your Wayfarer and meet other players.",18))
    email = TideUI.edit("Email address")
    card.add_child(email)
    password = TideUI.edit("Password",true)
    card.add_child(password)
    display_name = TideUI.edit("Display name · new accounts")
    display_name.max_length = 64
    card.add_child(display_name)
    card.add_child(TideUI.button("Sign in",authenticate.bind(false),true))
    card.add_child(TideUI.button("Create account",authenticate.bind(true)))
    card.add_child(TideUI.button("Explore the offline preview",start_preview))
    card.add_child(TideUI.button("Server connection",show_connection))
    add_status("Online play requires the matching Veilbound Tides server update.")

func show_connection() -> void:
    clear_card("Server connection")
    card.add_child(TideUI.paragraph("Enter the HTTPS API address of your Veilbound Tides server. Localhost HTTP is allowed only in development builds.",18))
    var field = TideUI.edit("https://server.example/api/v1")
    field.text = server_url
    card.add_child(field)
    card.add_child(TideUI.button("Save connection",func():
        server_url = field.text.strip_edges().trim_suffix("/")
        var config = ConfigFile.new()
        config.load("user://settings.cfg")
        config.set_value("network","server",server_url)
        config.save("user://settings.cfg")
        show_login(),true))
    card.add_child(TideUI.button("Back",show_login))
    add_status()

func authenticate(registering: bool) -> void:
    if busy:
        return
    if email.text.strip_edges().is_empty() or password.text.length() < 8:
        status_label.text = "Enter your email and a password of at least 8 characters."
        return
    if registering and display_name.text.strip_edges().length() < 2:
        status_label.text = "Choose a display name with at least 2 characters."
        return
    busy = true
    status_label.text = "Checking server…"
    ApiClient.set_session(server_url,"")
    var info = await ApiClient.get_json("/server-info")
    if info.is_empty() or info.get("world_protocol",0) != 1 or info.get("story_protocol",0) != 1 or info.get("folio_protocol",0) != 1:
        if not info.is_empty():
            status_label.text = "Update the server for this game build, then try again."
        busy = false
        return
    status_label.text = "Opening your account…"
    var payload = {"email":email.text.strip_edges(),"password":password.text}
    if registering:
        payload["display_name"] = display_name.text.strip_edges()
    var auth = await ApiClient.post_json("/auth/register" if registering else "/auth/login",payload)
    busy = false
    if auth.is_empty():
        return
    password.text = ""
    ApiClient.access_token = auth.access_token
    var catalog = await ApiClient.get_json("/content")
    if catalog.has("data"):
        var original_geometry = world.geometry
        GameData.set_definitions(catalog.data)
        if GameData.definition("zones","dawnreef_atoll").rules.world != original_geometry:
            status_label.text = "The server's world layout changed. Install the matching client build."
            return
    var characters = await ApiClient.get_json("/characters")
    if not characters.has("data"):
        return
    if characters.data.is_empty():
        show_creator()
    else:
        show_character(characters.data[0])

func show_creator() -> void:
    clear_card("Make your Wayfarer")
    var name_field = TideUI.edit("Character name · 2–24 characters")
    name_field.max_length = 24
    card.add_child(name_field)
    card.add_child(TideUI.label("Your first affinity",18,TideUI.GOLD))
    var affinity = TideUI.option(["Lanterncraft · reveal & focus","Rootbinding · restrain & protect","Tideseaming · mend & redirect"])
    card.add_child(affinity)
    card.add_child(TideUI.paragraph("All Wayfarers begin with Glimmer Spark, Root Snare and Tide Mend. Affinity is a starting identity; cross-training will grow later.",16))
    var robe = TideUI.option(["Reef teal robe","Warm coral robe","Evening indigo robe"])
    card.add_child(robe)
    var skin = TideUI.option(["Warm skin","Deep skin","Pale skin"])
    card.add_child(skin)
    card.add_child(TideUI.button("Create Wayfarer",func(): create_character(name_field.text,affinity.selected,robe.selected,skin.selected),true))
    add_status()

func create_character(character_name: String, affinity: int, robe: int, skin: int) -> void:
    if busy:
        return
    busy = true
    status_label.text = "Saving your Wayfarer…"
    var result = await ApiClient.post_json("/characters",{"name":character_name,"affinity":["lanterncraft","rootbinding","tideseaming"][affinity],"appearance":{"robe":["teal","coral","indigo"][robe],"skin":["warm","deep","pale"][skin]}})
    busy = false
    if not result.is_empty():
        show_character(result)

func show_character(character: Dictionary) -> void:
    selected_character = character
    clear_card("Welcome, " + character.name)
    card.add_child(TideUI.paragraph("Level %s · %s\nDawnreef Atoll awaits." % [character.level,character.get("affinity","lanterncraft").capitalize()],22))
    card.add_child(TideUI.button("Enter Dawnreef",enter_world,true))
    card.add_child(TideUI.button("Sign out",sign_out))
    add_status()

func enter_world() -> void:
    if busy:
        return
    busy = true
    status_label.text = "Entering Dawnreef…"
    var result = await ApiClient.get_json("/world/characters/"+selected_character.id)
    busy = false
    if not result.is_empty():
        _play(result,false)

func start_preview() -> void:
    if busy:
        return
    GameData.load_bundle()
    _play({"id":"preview","name":"Visiting Wayfarer","level":1,"appearance":{"robe":"teal","skin":"warm"},"position":{"x":0,"z":4},"quest_state":{},"wallet":{},"inventory":{}},true)

func _play(character: Dictionary, offline: bool) -> void:
    gateway.hide()
    session = PlaySession.new()
    add_child(session)
    session.return_requested.connect(return_to_gateway)
    session.begin(world,character,offline)
    if offline and OS.has_feature("debug"):
        print("VT_PREVIEW_READY")

func return_to_gateway() -> void:
    if is_instance_valid(session):
        remove_child(session)
        session.queue_free()
        session = null
    panorama.current = true
    gateway.show()
    show_login()

func sign_out() -> void:
    await ApiClient.post_json("/auth/logout",{})
    ApiClient.access_token = ""
    show_login()

func _request_failed(_endpoint: String, code: int, message: String) -> void:
    var words = "Unable to reach the server. Check your connection and server address."
    if code > 0:
        var parsed = JSON.parse_string(message)
        words = str(parsed.get("detail","The request could not be completed.")) if parsed is Dictionary else "The server could not complete the request."
    if is_instance_valid(status_label):
        status_label.text = words
    if is_instance_valid(session) and is_instance_valid(session.hud):
        session.hud.quest_label.text = words
