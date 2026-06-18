extends Control

const DEFAULT_API_URL := "https://game.surveyroute.work/api/v1"
const STARTER_QUEST_KEY := "lantern_well_first_light"
const STARTER_ENEMY_KEY := "fog_thorn_lurker"
const STARTER_SPELL_KEY := "root_snare"
const SPELL_GLIMMER_SPARK := "glimmer_spark"
const SPELL_ROOT_SNARE := "root_snare"
const SPELL_TIDE_MEND := "tide_mend"
const PLAYER_SPEED := 4.0
const INTERACTION_RANGE := 1.5
const NPC_POSITION := Vector3(-3, 0.5, -1.6)
const ENEMY_POSITION := Vector3(3, 0.5, -1.8)
const TRAVEL_GATE_POSITION := Vector3(0, 0.5, 6.2)
const MARKET_GUIDE_POSITION := Vector3(-6.2, 0.5, 0.6)
const TRAINER_POSITION := Vector3(6.2, 0.5, 0.6)
const DOCK_GUIDE_POSITION := Vector3(0, 0.5, 8.2)
const COLOR_BG := Color(0.08, 0.10, 0.16)
const COLOR_PANEL := Color(0.12, 0.14, 0.22, 0.94)
const COLOR_PANEL_ACCENT := Color(0.21, 0.18, 0.32, 0.96)
const COLOR_GOLD := Color(1.0, 0.76, 0.32)
const COLOR_TEXT := Color(0.93, 0.90, 0.82)
const COLOR_BUTTON := Color(0.25, 0.22, 0.38)
const COLOR_BUTTON_HOVER := Color(0.36, 0.30, 0.52)

var account := {}
var character := {}
var access_token := ""
var world_active := false
var touch_move := Vector2.ZERO
var joystick_touching := false

var root: VBoxContainer
var splash_screen: VBoxContainer
var auth_screen: VBoxContainer
var character_screen: VBoxContainer
var world_screen: VBoxContainer
var player_marker: MeshInstance3D
var enemy_marker: MeshInstance3D
var camera: Camera3D
var viewport_container: SubViewportContainer
var joystick_knob: ColorRect
var api_url_input: LineEdit
var email_input: LineEdit
var password_input: LineEdit
var display_name_input: LineEdit
var character_name_input: LineEdit
var ancestry_option: OptionButton
var origin_option: OptionButton
var character_card: RichTextLabel
var enter_world_button: Button
var status_label: Label
var interaction_label: Label
var profile_label: RichTextLabel
var minimap_label: RichTextLabel
var quest_tracker_label: RichTextLabel
var talk_button: Button
var fight_button: Button
var dialogue_accept_button: Button
var dialogue_panel: PanelContainer
var dialogue_text: RichTextLabel
var combat_panel: PanelContainer
var combat_text: RichTextLabel
var secondary_tray: GridContainer
var character_summary: RichTextLabel
var quest_summary: RichTextLabel
var inventory_summary: RichTextLabel
var event_log: RichTextLabel


func _ready() -> void:
    ApiClient.request_failed.connect(_on_request_failed)
    _build_ui()
    _set_status("Ready. Register or login to begin.")


func _process(delta: float) -> void:
    if not world_active or player_marker == null:
        return
    _move_player(delta)
    _update_interaction_prompt()


func _build_ui() -> void:
    var background := ColorRect.new()
    background.color = COLOR_BG
    background.set_anchors_preset(Control.PRESET_FULL_RECT)
    add_child(background)

    root = VBoxContainer.new()
    root.set_anchors_preset(Control.PRESET_FULL_RECT)
    root.offset_left = 14
    root.offset_top = 14
    root.offset_right = -14
    root.offset_bottom = -14
    root.add_theme_constant_override("separation", 10)
    add_child(root)

    var title := Label.new()
    title.text = "Veilbound Tides"
    title.add_theme_font_size_override("font_size", 24)
    title.add_theme_color_override("font_color", COLOR_GOLD)
    root.add_child(title)

    status_label = Label.new()
    status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    status_label.add_theme_color_override("font_color", COLOR_TEXT)
    root.add_child(status_label)

    _build_auth_screen()
    _build_character_screen()
    _build_world_screen()
    _build_splash_screen()
    _show_splash_screen()


func _build_splash_screen() -> void:
    splash_screen = VBoxContainer.new()
    splash_screen.add_theme_constant_override("separation", 14)
    root.add_child(splash_screen)

    var logo := Label.new()
    logo.text = "VEILBOUND TIDES"
    logo.add_theme_font_size_override("font_size", 34)
    logo.add_theme_color_override("font_color", COLOR_GOLD)
    splash_screen.add_child(logo)

    var tagline := Label.new()
    tagline.text = "Auralis awaits beyond the lantern reefs."
    tagline.add_theme_font_size_override("font_size", 18)
    tagline.add_theme_color_override("font_color", COLOR_TEXT)
    tagline.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    splash_screen.add_child(tagline)

    var start_button := Button.new()
    start_button.text = "Tap to Begin"
    start_button.custom_minimum_size = Vector2(260, 60)
    _style_button(start_button)
    start_button.pressed.connect(Callable(self, "_show_auth_screen"))
    splash_screen.add_child(start_button)


func _build_auth_screen() -> void:
    auth_screen = VBoxContainer.new()
    auth_screen.add_theme_constant_override("separation", 10)
    root.add_child(auth_screen)

    var gateway_title := Label.new()
    gateway_title.text = "Wayfarer Account Gateway"
    gateway_title.add_theme_font_size_override("font_size", 22)
    gateway_title.add_theme_color_override("font_color", COLOR_GOLD)
    auth_screen.add_child(gateway_title)

    var description := Label.new()
    description.text = "Enter Auralis through a live account. New Wayfarers register; returning players login to continue saved progress."
    description.add_theme_color_override("font_color", COLOR_TEXT)
    auth_screen.add_child(description)

    api_url_input = _line_edit(DEFAULT_API_URL, "API base URL")
    auth_screen.add_child(_labeled_row("API", api_url_input))

    email_input = _line_edit("player%s@example.com" % Time.get_unix_time_from_system(), "Email")
    auth_screen.add_child(_labeled_row("Email", email_input))

    password_input = _line_edit("safe-password", "Password")
    password_input.secret = true
    auth_screen.add_child(_labeled_row("Password", password_input))

    display_name_input = _line_edit("Player%s" % Time.get_unix_time_from_system(), "Display name")
    auth_screen.add_child(_labeled_row("Display", display_name_input))

    auth_screen.add_child(_button_row([
        ["Register", Callable(self, "_on_register_pressed")],
        ["Login", Callable(self, "_on_login_pressed")],
    ]))


func _build_character_screen() -> void:
    character_screen = VBoxContainer.new()
    character_screen.add_theme_constant_override("separation", 10)
    root.add_child(character_screen)

    var lobby_title := Label.new()
    lobby_title.text = "Wayfarer Hall"
    lobby_title.add_theme_font_size_override("font_size", 22)
    lobby_title.add_theme_color_override("font_color", COLOR_GOLD)
    character_screen.add_child(lobby_title)

    var description := Label.new()
    description.text = "Choose a saved Wayfarer or create the first character for this account."
    description.add_theme_color_override("font_color", COLOR_TEXT)
    character_screen.add_child(description)

    character_card = _rich_panel()
    character_screen.add_child(character_card)

    character_name_input = _line_edit("Ari%s" % Time.get_unix_time_from_system(), "Character name")
    character_screen.add_child(_labeled_row("Character", character_name_input))

    ancestry_option = OptionButton.new()
    ancestry_option.add_item("Lumenfolk", 0)
    ancestry_option.set_item_metadata(0, "lumenfolk")
    ancestry_option.add_item("Brindlekin", 1)
    ancestry_option.set_item_metadata(1, "brindlekin")
    ancestry_option.add_item("Orran", 2)
    ancestry_option.set_item_metadata(2, "orran")
    ancestry_option.add_item("Tideveiled", 3)
    ancestry_option.set_item_metadata(3, "tideveiled")
    _style_option_button(ancestry_option)
    character_screen.add_child(_labeled_row("People", ancestry_option))

    origin_option = OptionButton.new()
    origin_option.add_item("Dawnreef Local", 0)
    origin_option.set_item_metadata(0, "dawnreef_local")
    origin_option.add_item("Glasswake Apprentice", 1)
    origin_option.set_item_metadata(1, "glasswake_apprentice")
    origin_option.add_item("Rootbound Scout", 2)
    origin_option.set_item_metadata(2, "rootbound_scout")
    _style_option_button(origin_option)
    character_screen.add_child(_labeled_row("Origin", origin_option))

    enter_world_button = Button.new()
    enter_world_button.text = "Enter World"
    enter_world_button.pressed.connect(Callable(self, "_on_enter_world_pressed"))
    _style_button(enter_world_button)
    character_screen.add_child(enter_world_button)

    character_screen.add_child(_button_row([
        ["Create New Character", Callable(self, "_on_create_character_pressed")],
        ["Logout", Callable(self, "_on_logout_pressed")],
    ]))


func _build_world_screen() -> void:
    world_screen = VBoxContainer.new()
    world_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
    world_screen.add_theme_constant_override("separation", 8)
    root.add_child(world_screen)

    var top_hud := HBoxContainer.new()
    top_hud.add_theme_constant_override("separation", 8)
    world_screen.add_child(top_hud)

    profile_label = _compact_panel()
    profile_label.custom_minimum_size = Vector2(260, 80)
    top_hud.add_child(profile_label)

    quest_tracker_label = _compact_panel()
    quest_tracker_label.custom_minimum_size = Vector2(360, 80)
    quest_tracker_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    top_hud.add_child(quest_tracker_label)

    minimap_label = _compact_panel()
    minimap_label.custom_minimum_size = Vector2(180, 80)
    top_hud.add_child(minimap_label)

    viewport_container = SubViewportContainer.new()
    viewport_container.stretch = true
    viewport_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    viewport_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
    viewport_container.custom_minimum_size = Vector2(0, 320)
    viewport_container.add_theme_stylebox_override("panel", _style_box(Color(0.05, 0.07, 0.12), 10))
    viewport_container.gui_input.connect(Callable(self, "_on_world_view_input"))
    world_screen.add_child(viewport_container)

    var viewport := SubViewport.new()
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport_container.add_child(viewport)
    _build_placeholder_world(viewport)

    var controls_bar := VBoxContainer.new()
    controls_bar.add_theme_constant_override("separation", 8)
    world_screen.add_child(controls_bar)

    var top_action_row := HBoxContainer.new()
    top_action_row.add_theme_constant_override("separation", 8)
    controls_bar.add_child(top_action_row)

    var hud := VBoxContainer.new()
    hud.add_theme_constant_override("separation", 10)

    var hud_scroll := ScrollContainer.new()
    hud_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    hud_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    hud_scroll.add_child(hud)
    world_screen.add_child(hud_scroll)

    var hud_title := Label.new()
    hud_title.text = "Dawnreef Commons"
    hud_title.add_theme_font_size_override("font_size", 22)
    hud_title.add_theme_color_override("font_color", COLOR_GOLD)
    hud.add_child(hud_title)

    interaction_label = Label.new()
    interaction_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    interaction_label.add_theme_color_override("font_color", COLOR_TEXT)
    controls_bar.add_child(interaction_label)

    character_summary = _rich_panel()
    quest_summary = _rich_panel()
    inventory_summary = _rich_panel()
    event_log = _rich_panel()
    event_log.size_flags_vertical = Control.SIZE_EXPAND_FILL

    var movement_hint := Label.new()
    movement_hint.text = "Move: WASD, arrow keys, or the on-screen controls."
    movement_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    movement_hint.add_theme_color_override("font_color", COLOR_TEXT)
    controls_bar.add_child(movement_hint)

    controls_bar.add_child(_virtual_joystick())

    var action_row := _button_row([
        ["Refresh World", Callable(self, "_on_enter_world_pressed")],
        ["Save", Callable(self, "_on_save_pressed")],
        ["Logout", Callable(self, "_on_logout_pressed")],
    ])
    top_action_row.add_child(action_row)

    talk_button = Button.new()
    talk_button.text = "Talk to Mara"
    talk_button.pressed.connect(Callable(self, "_open_dialogue_panel"))
    _style_button(talk_button)
    top_action_row.add_child(talk_button)

    fight_button = Button.new()
    fight_button.text = "Fight Fog-Thorn"
    fight_button.pressed.connect(Callable(self, "_open_combat_panel"))
    _style_button(fight_button)
    top_action_row.add_child(fight_button)

    hud.add_child(character_summary)
    hud.add_child(quest_summary)
    hud.add_child(inventory_summary)

    dialogue_panel = _panel_box()
    var dialogue_layout := VBoxContainer.new()
    dialogue_layout.add_theme_constant_override("separation", 8)
    dialogue_panel.add_child(dialogue_layout)
    dialogue_text = _rich_panel()
    dialogue_layout.add_child(dialogue_text)
    var dialogue_actions := HBoxContainer.new()
    dialogue_actions.add_theme_constant_override("separation", 8)
    dialogue_accept_button = Button.new()
    dialogue_accept_button.text = "Accept Quest"
    dialogue_accept_button.pressed.connect(Callable(self, "_on_accept_quest_pressed"))
    dialogue_actions.add_child(dialogue_accept_button)
    var close_dialogue_button := Button.new()
    close_dialogue_button.text = "Close"
    close_dialogue_button.pressed.connect(Callable(self, "_close_dialogue_panel"))
    dialogue_actions.add_child(close_dialogue_button)
    dialogue_layout.add_child(dialogue_actions)
    hud.add_child(dialogue_panel)

    combat_panel = _panel_box()
    var combat_layout := VBoxContainer.new()
    combat_layout.add_theme_constant_override("separation", 8)
    combat_panel.add_child(combat_layout)
    combat_text = _rich_panel()
    combat_layout.add_child(combat_text)
    combat_layout.add_child(_button_row([
        ["Glimmer Spark", Callable(self, "_on_cast_glimmer_spark")],
        ["Root Snare", Callable(self, "_on_cast_root_snare")],
        ["Tide Mend", Callable(self, "_on_cast_tide_mend")],
        ["Close", Callable(self, "_close_combat_panel")],
    ]))
    hud.add_child(combat_panel)

    hud.add_child(event_log)
    _close_dialogue_panel()
    _close_combat_panel()

    world_screen.add_child(_bottom_action_bar())
    secondary_tray = _secondary_tray()
    secondary_tray.visible = false
    world_screen.add_child(secondary_tray)


func _build_placeholder_world(viewport: SubViewport) -> void:
    var world := Node3D.new()
    viewport.add_child(world)

    var environment := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.12, 0.18, 0.28)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.55, 0.62, 0.78)
    env.ambient_light_energy = 0.7
    environment.environment = env
    world.add_child(environment)

    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-55, 35, 0)
    light.light_energy = 2.0
    world.add_child(light)

    camera = Camera3D.new()
    camera.position = Vector3(0, 7, 9)
    camera.rotation_degrees = Vector3(-38, 0, 0)
    camera.current = true
    world.add_child(camera)

    var ground := MeshInstance3D.new()
    var plane := PlaneMesh.new()
    plane.size = Vector2(22, 22)
    ground.mesh = plane
    ground.material_override = _material(Color(0.24, 0.45, 0.34))
    world.add_child(ground)

    _add_box_prop(world, "Glimmerdeep Water", Vector3(0, -0.06, 0), Vector3(24.0, 0.04, 24.0), Color(0.05, 0.20, 0.32))
    _add_box_prop(world, "Dawnreef Main Walkway", Vector3(0, 0.02, -1.65), Vector3(9.2, 0.05, 0.8), Color(0.78, 0.64, 0.42))
    _add_box_prop(world, "North Reef Path", Vector3(0, 0.025, 2.2), Vector3(1.0, 0.05, 5.6), Color(0.70, 0.58, 0.38))
    _add_box_prop(world, "West Market Path", Vector3(-4.0, 0.025, 0.6), Vector3(3.6, 0.05, 0.7), Color(0.70, 0.58, 0.38))
    _add_box_prop(world, "East Training Path", Vector3(4.0, 0.025, 0.6), Vector3(3.6, 0.05, 0.7), Color(0.70, 0.58, 0.38))
    _add_box_prop(world, "Lantern Well Base", Vector3(0, 0.18, -1.65), Vector3(1.2, 0.34, 1.2), Color(0.32, 0.30, 0.38))
    _add_box_prop(world, "Lantern Well Light", Vector3(0, 0.85, -1.65), Vector3(0.42, 0.9, 0.42), Color(1.0, 0.78, 0.25))

    _add_box_prop(world, "Welcome Arch Left", Vector3(-1.4, 0.8, -4.6), Vector3(0.24, 1.6, 0.24), Color(0.42, 0.30, 0.48))
    _add_box_prop(world, "Welcome Arch Right", Vector3(1.4, 0.8, -4.6), Vector3(0.24, 1.6, 0.24), Color(0.42, 0.30, 0.48))
    _add_box_prop(world, "Welcome Arch Top", Vector3(0, 1.65, -4.6), Vector3(1.65, 0.18, 0.22), Color(0.50, 0.35, 0.58))
    _add_box_prop(world, "Training Ring", Vector3(5.4, 0.04, 0.6), Vector3(1.2, 0.06, 1.2), Color(0.55, 0.35, 0.28))
    _add_box_prop(world, "Market Awning", Vector3(-5.4, 0.7, 0.6), Vector3(1.3, 0.18, 0.9), Color(0.82, 0.42, 0.36))

    for offset in [-6.4, -5.7, -4.8, -4.1, 4.1, 4.8, 5.7, 6.4]:
        _add_box_prop(world, "Sunthread Reeds", Vector3(offset, 0.35, 1.7), Vector3(0.16, 0.7, 0.16), Color(0.86, 0.68, 0.30))

    _add_box_prop(world, "Blue Veil Crystal", Vector3(-2.2, 0.55, 2.4), Vector3(0.32, 1.1, 0.32), Color(0.32, 0.75, 1.0))
    _add_box_prop(world, "Violet Veil Crystal", Vector3(2.2, 0.45, 2.1), Vector3(0.28, 0.9, 0.28), Color(0.72, 0.44, 1.0))
    _add_box_prop(world, "Travel Gate Pillar A", Vector3(-0.9, 0.95, 6.2), Vector3(0.28, 1.9, 0.28), Color(0.30, 0.62, 0.92))
    _add_box_prop(world, "Travel Gate Pillar B", Vector3(0.9, 0.95, 6.2), Vector3(0.28, 1.9, 0.28), Color(0.30, 0.62, 0.92))
    _add_box_prop(world, "Travel Gate Glow", TRAVEL_GATE_POSITION + Vector3(0, 0.85, 0), Vector3(0.75, 1.3, 0.12), Color(0.42, 0.88, 1.0))
    _add_box_prop(world, "Dock Planks", Vector3(0, 0.03, 8.4), Vector3(2.4, 0.05, 1.2), Color(0.46, 0.34, 0.22))
    _add_box_prop(world, "Crafting Canopy", Vector3(-2.8, 0.75, 4.0), Vector3(1.2, 0.16, 0.8), Color(0.36, 0.62, 0.42))
    _add_box_prop(world, "Residential Lantern", Vector3(2.9, 0.8, 4.0), Vector3(0.32, 1.1, 0.32), Color(1.0, 0.66, 0.22))
    _add_label(world, "Dawnreef Commons", Vector3(0, 1.2, -4.6), COLOR_GOLD)
    _add_label(world, "Market", Vector3(-5.4, 1.25, 0.6), Color.WHITE)
    _add_label(world, "Training Ring", Vector3(5.4, 1.15, 0.6), Color.WHITE)
    _add_label(world, "Travel Gate", TRAVEL_GATE_POSITION + Vector3(0, 1.8, 0), Color(0.58, 0.9, 1.0))
    _add_label(world, "Docks", DOCK_GUIDE_POSITION + Vector3(0, 1.4, 0), Color.WHITE)
    _add_label(world, "Crafting Quarter", Vector3(-2.8, 1.3, 4.0), Color.WHITE)

    player_marker = _add_marker(world, "Player", Vector3(0, 0.7, 0), Color(0.3, 0.65, 1.0), CapsuleMesh.new())
    _add_marker(world, "Mara NPC", NPC_POSITION, Color(1.0, 0.78, 0.25), SphereMesh.new())
    enemy_marker = _add_marker(world, "Fog-Thorn Enemy", ENEMY_POSITION, Color(0.8, 0.25, 0.25), BoxMesh.new())
    _add_marker(world, "Tallo Reedcart", MARKET_GUIDE_POSITION, Color(0.95, 0.45, 0.28), SphereMesh.new())
    _add_marker(world, "Instructor Veyra", TRAINER_POSITION, Color(0.56, 0.42, 1.0), CapsuleMesh.new())
    _add_marker(world, "Guide Pella", DOCK_GUIDE_POSITION, Color(0.35, 0.85, 0.82), SphereMesh.new())
    _add_marker(world, "Gatekeeper Orris", TRAVEL_GATE_POSITION, Color(0.42, 0.8, 1.0), CapsuleMesh.new())
    _update_interaction_prompt()


func _add_marker(world: Node3D, label_text: String, position: Vector3, color: Color, mesh: Mesh) -> MeshInstance3D:
    var marker := MeshInstance3D.new()
    marker.name = label_text
    marker.position = position
    marker.mesh = mesh
    marker.material_override = _material(color)
    world.add_child(marker)

    var label := Label3D.new()
    label.text = label_text
    label.position = position + Vector3(0, 1.1, 0)
    label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
    label.modulate = Color.WHITE
    world.add_child(label)
    return marker


func _add_label(world: Node3D, text: String, position: Vector3, color: Color) -> Label3D:
    var label := Label3D.new()
    label.text = text
    label.position = position
    label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
    label.modulate = color
    world.add_child(label)
    return label


func _add_box_prop(world: Node3D, prop_name: String, position: Vector3, scale_value: Vector3, color: Color) -> MeshInstance3D:
    var prop := MeshInstance3D.new()
    prop.name = prop_name
    prop.position = position
    prop.scale = scale_value
    prop.mesh = BoxMesh.new()
    prop.material_override = _material(color)
    world.add_child(prop)
    return prop


func _material(color: Color) -> StandardMaterial3D:
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.roughness = 0.75
    return material


func _line_edit(text: String, placeholder: String) -> LineEdit:
    var input := LineEdit.new()
    input.text = text
    input.placeholder_text = placeholder
    input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    input.add_theme_stylebox_override("normal", _style_box(Color(0.06, 0.07, 0.11), 6))
    input.add_theme_stylebox_override("focus", _style_box(Color(0.10, 0.11, 0.18), 6))
    input.add_theme_color_override("font_color", COLOR_TEXT)
    input.add_theme_color_override("font_placeholder_color", Color(0.65, 0.62, 0.58))
    return input


func _labeled_row(label_text: String, input: Control) -> HBoxContainer:
    var row := HBoxContainer.new()
    var label := Label.new()
    label.text = label_text
    label.custom_minimum_size = Vector2(110, 0)
    label.add_theme_color_override("font_color", COLOR_TEXT)
    row.add_child(label)
    row.add_child(input)
    return row


func _button_row(buttons: Array) -> HBoxContainer:
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 8)
    for button_data in buttons:
        var button := Button.new()
        button.text = button_data[0]
        button.custom_minimum_size = Vector2(132, 52)
        _style_button(button)
        button.pressed.connect(button_data[1])
        row.add_child(button)
    return row


func _bottom_action_bar() -> HBoxContainer:
    var bar := HBoxContainer.new()
    bar.add_theme_constant_override("separation", 8)
    bar.add_theme_stylebox_override("panel", _style_box(Color(0.07, 0.08, 0.13, 0.96), 12))
    var slots := [
        ["Spark", Callable(self, "_on_cast_glimmer_spark")],
        ["Snare", Callable(self, "_on_cast_root_snare")],
        ["Mend", Callable(self, "_on_cast_tide_mend")],
        ["Quest", Callable(self, "_open_dialogue_panel")],
        ["Map", Callable(self, "_focus_travel_gate")],
        ["Menu", Callable(self, "_show_stub_menu")],
    ]
    for slot in slots:
        var button := Button.new()
        button.text = slot[0]
        button.custom_minimum_size = Vector2(96, 58)
        _style_button(button)
        button.pressed.connect(slot[1])
        bar.add_child(button)
    return bar


func _secondary_tray() -> GridContainer:
    var tray := GridContainer.new()
    tray.columns = 4
    tray.add_theme_constant_override("h_separation", 8)
    tray.add_theme_constant_override("v_separation", 8)
    var entries := [
        "Inventory",
        "Character",
        "Collections",
        "Mounts",
        "Friends",
        "Mail",
        "Settings",
        "Nearby",
    ]
    for entry in entries:
        var entry_name: String = entry
        var button := Button.new()
        button.text = entry_name
        button.custom_minimum_size = Vector2(132, 48)
        _style_button(button)
        button.pressed.connect(func() -> void:
            _set_event_log("[b]%s[/b]\nThis mobile MMO menu is reserved for the next backend/client milestone." % entry_name)
        )
        tray.add_child(button)
    return tray


func _virtual_joystick() -> PanelContainer:
    var panel := PanelContainer.new()
    panel.custom_minimum_size = Vector2(170, 170)
    panel.add_theme_stylebox_override("panel", _style_box(Color(0.06, 0.08, 0.13, 0.78), 85))
    panel.gui_input.connect(Callable(self, "_on_joystick_input"))

    var center := CenterContainer.new()
    panel.add_child(center)
    joystick_knob = ColorRect.new()
    joystick_knob.color = Color(0.55, 0.72, 1.0, 0.85)
    joystick_knob.custom_minimum_size = Vector2(54, 54)
    center.add_child(joystick_knob)
    return panel


func _on_joystick_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        joystick_touching = event.pressed
        if not joystick_touching:
            touch_move = Vector2.ZERO
            return
    if event is InputEventMouseMotion or event is InputEventMouseButton:
        var local_event = event as InputEvent
        var event_position := Vector2.ZERO
        if local_event is InputEventMouseMotion:
            event_position = (local_event as InputEventMouseMotion).position
        elif local_event is InputEventMouseButton:
            event_position = (local_event as InputEventMouseButton).position
        var center := Vector2(85, 85)
        var delta := (event_position - center) / 70.0
        touch_move = _clamp_touch_move(delta)


func _on_world_view_input(event: InputEvent) -> void:
    if not world_active or camera == null:
        return
    if event is InputEventMouseButton and event.pressed:
        var position := (event as InputEventMouseButton).position
        if position.distance_to(camera.unproject_position(NPC_POSITION)) < 58.0:
            _open_dialogue_panel()
        elif position.distance_to(camera.unproject_position(ENEMY_POSITION)) < 58.0:
            _open_combat_panel()
        elif position.distance_to(camera.unproject_position(TRAVEL_GATE_POSITION)) < 58.0:
            _set_event_log("[b]Travel Gate[/b]\nThe gate hums softly. Region travel will unlock in a later milestone.")
        elif position.distance_to(camera.unproject_position(MARKET_GUIDE_POSITION)) < 58.0:
            _set_event_log("[b]Tallo Reedcart[/b]\n\"Fresh wraps, reedcloth, and lantern oil. Shops are coming soon.\"")
        elif position.distance_to(camera.unproject_position(TRAINER_POSITION)) < 58.0:
            _set_event_log("[b]Instructor Veyra[/b]\n\"Keep your stance loose. Your next ability unlocks after more training.\"")


func _style_button(button: Button) -> void:
    button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    button.add_theme_stylebox_override("normal", _style_box(COLOR_BUTTON, 8))
    button.add_theme_stylebox_override("hover", _style_box(COLOR_BUTTON_HOVER, 8))
    button.add_theme_stylebox_override("pressed", _style_box(Color(0.18, 0.16, 0.28), 8))
    button.add_theme_color_override("font_color", COLOR_TEXT)
    button.add_theme_color_override("font_hover_color", Color.WHITE)


func _style_option_button(option: OptionButton) -> void:
    option.add_theme_stylebox_override("normal", _style_box(Color(0.06, 0.07, 0.11), 6))
    option.add_theme_stylebox_override("hover", _style_box(COLOR_BUTTON_HOVER, 6))
    option.add_theme_color_override("font_color", COLOR_TEXT)


func _selected_metadata(option: OptionButton) -> String:
    var metadata = option.get_item_metadata(option.selected)
    return str(metadata)


func _style_box(color: Color, radius: int) -> StyleBoxFlat:
    var box := StyleBoxFlat.new()
    box.bg_color = color
    box.border_color = Color(0.75, 0.58, 0.28, 0.65)
    box.set_border_width_all(1)
    box.set_corner_radius_all(radius)
    box.set_content_margin(SIDE_LEFT, 10)
    box.set_content_margin(SIDE_RIGHT, 10)
    box.set_content_margin(SIDE_TOP, 8)
    box.set_content_margin(SIDE_BOTTOM, 8)
    return box


func _movement_pad() -> HBoxContainer:
    var pad := HBoxContainer.new()
    pad.add_theme_constant_override("separation", 8)
    pad.add_child(_movement_button("Left", Vector2(-1, 0)))
    pad.add_child(_movement_button("Up", Vector2(0, -1)))
    pad.add_child(_movement_button("Down", Vector2(0, 1)))
    pad.add_child(_movement_button("Right", Vector2(1, 0)))
    return pad


func _movement_button(label_text: String, direction: Vector2) -> Button:
    var button := Button.new()
    button.text = label_text
    button.custom_minimum_size = Vector2(112, 54)
    _style_button(button)
    button.button_down.connect(func() -> void:
        touch_move = _clamp_touch_move(touch_move + direction)
    )
    button.button_up.connect(func() -> void:
        touch_move = _clamp_touch_move(touch_move - direction)
    )
    return button


func _clamp_touch_move(value: Vector2) -> Vector2:
    return Vector2(clamp(value.x, -1.0, 1.0), clamp(value.y, -1.0, 1.0))


func _panel_box() -> PanelContainer:
    var panel := PanelContainer.new()
    panel.visible = false
    panel.add_theme_stylebox_override("panel", _style_box(COLOR_PANEL_ACCENT, 10))
    return panel


func _move_player(delta: float) -> void:
    var direction := Vector3.ZERO
    if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
        direction.z -= 1.0
    if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
        direction.z += 1.0
    if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
        direction.x -= 1.0
    if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
        direction.x += 1.0
    direction.x += touch_move.x
    direction.z += touch_move.y

    if direction == Vector3.ZERO:
        return

    direction = direction.normalized()
    player_marker.position += direction * PLAYER_SPEED * delta
    player_marker.position.x = clamp(player_marker.position.x, -9.5, 9.5)
    player_marker.position.z = clamp(player_marker.position.z, -9.5, 9.5)
    camera.position.x = player_marker.position.x
    camera.position.z = player_marker.position.z + 9.0


func _update_interaction_prompt() -> void:
    if interaction_label == null or player_marker == null or talk_button == null or fight_button == null:
        return

    var near_npc := _is_player_near(NPC_POSITION)
    var near_enemy := _is_player_near(ENEMY_POSITION)
    talk_button.visible = near_npc
    fight_button.visible = near_enemy

    if near_npc:
        interaction_label.text = "Near Mara Lanternwright. Press Talk to open dialogue."
    elif near_enemy:
        interaction_label.text = "Near Fog-Thorn Lurker. Press Fight to choose a spell."
    else:
        interaction_label.text = "Move with WASD or arrow keys. Walk to Mara or the Fog-Thorn marker."
        _close_dialogue_panel()
        _close_combat_panel()


func _is_player_near(target: Vector3) -> bool:
    var player_position := Vector2(player_marker.position.x, player_marker.position.z)
    var target_position := Vector2(target.x, target.z)
    return player_position.distance_to(target_position) <= INTERACTION_RANGE


func _rich_panel() -> RichTextLabel:
    var panel := RichTextLabel.new()
    panel.bbcode_enabled = true
    panel.fit_content = true
    panel.scroll_active = true
    panel.custom_minimum_size = Vector2(0, 90)
    panel.add_theme_stylebox_override("normal", _style_box(COLOR_PANEL, 10))
    panel.add_theme_color_override("default_color", COLOR_TEXT)
    return panel


func _on_register_pressed() -> void:
    _configure_api("")
    _set_status("Registering account...")
    var response := await ApiClient.post_json("/auth/register", {
        "email": email_input.text,
        "display_name": display_name_input.text,
        "password": password_input.text,
    })
    _handle_auth_response(response, "Registered.")


func _on_login_pressed() -> void:
    _configure_api("")
    _set_status("Logging in...")
    var response := await ApiClient.post_json("/auth/login", {
        "email": email_input.text,
        "password": password_input.text,
    })
    _handle_auth_response(response, "Logged in.")


func _on_create_character_pressed() -> void:
    if not _require_token():
        return
    _set_status("Creating character...")
    var response := await ApiClient.post_json("/characters", {
        "name": character_name_input.text,
        "ancestry_key": _selected_metadata(ancestry_option),
        "origin_key": _selected_metadata(origin_option),
    })
    if response.is_empty():
        return
    character = response
    _show_character_screen()
    _refresh_character_lobby("Character created. Enter the world when ready.")


func _on_enter_world_pressed() -> void:
    if not _require_character():
        return
    _set_status("Entering world...")
    var response := await ApiClient.get_json("/world/characters/%s" % character["id"])
    if response.is_empty():
        return
    character = response
    _show_world_screen()
    _show_character_state("Entered world.")


func _on_accept_quest_pressed() -> void:
    if not _require_character():
        return
    _set_status("Accepting quest...")
    _close_dialogue_panel()
    var response := await ApiClient.post_json(
        "/world/characters/%s/quests/%s/accept" % [character["id"], STARTER_QUEST_KEY],
        {}
    )
    if response.is_empty():
        return
    character = response
    _show_character_state("Quest accepted.")


func _on_fight_enemy_pressed() -> void:
    await _fight_with_spell(STARTER_SPELL_KEY)


func _on_cast_glimmer_spark() -> void:
    await _fight_with_spell(SPELL_GLIMMER_SPARK)


func _on_cast_root_snare() -> void:
    await _fight_with_spell(SPELL_ROOT_SNARE)


func _on_cast_tide_mend() -> void:
    await _fight_with_spell(SPELL_TIDE_MEND)


func _fight_with_spell(spell_key: String) -> void:
    if not _require_character():
        return
    _set_status("Casting %s..." % _spell_name(spell_key))
    var response := await ApiClient.post_json(
        "/world/characters/%s/combat/fight" % character["id"],
        {
            "enemy_key": STARTER_ENEMY_KEY,
            "spell_key": spell_key,
        }
    )
    if response.is_empty():
        return
    if response.has("character"):
        character = response["character"]
    _show_character_state("%s resolved." % _spell_name(spell_key))
    combat_text.text = "[b]Combat Result[/b]\n%s" % _fight_summary(response)
    _set_event_log(_fight_summary(response))
    await _pulse_enemy_marker()


func _on_save_pressed() -> void:
    if not _require_character():
        return
    _set_status("Saving progress...")
    var response := await ApiClient.post_json("/world/characters/%s/save" % character["id"], {})
    if response.is_empty():
        return
    character = response
    _show_character_state("Progress saved.")


func _on_logout_pressed() -> void:
    if not _require_token():
        return
    _set_status("Logging out...")
    var response := await ApiClient.post_json("/auth/logout", {})
    access_token = ""
    account = {}
    character = {}
    ApiClient.set_session(api_url_input.text, "")
    _close_dialogue_panel()
    _close_combat_panel()
    _show_auth_screen()
    _set_event_log(JSON.stringify(response, "\t"))


func _handle_auth_response(response: Dictionary, message: String) -> void:
    if response.is_empty():
        return
    account = response.get("account", {})
    access_token = response.get("access_token", "")
    _configure_api(access_token)
    _set_event_log(JSON.stringify(response, "\t"))
    await _load_existing_character_or_show_create(message)


func _load_existing_character_or_show_create(message: String) -> void:
    _set_status("%s Checking for characters..." % message)
    var response := await ApiClient.get_json("/characters")
    if response.has("data") and response["data"] is Array:
        var characters: Array = response["data"]
        if not characters.is_empty():
            character = characters[0]
            _show_character_screen()
            _refresh_character_lobby("%s Character loaded." % message)
            return
    _show_character_screen()
    _refresh_character_lobby("%s Create a character to enter Dawnreef." % message)


func _configure_api(token: String) -> void:
    ApiClient.set_session(api_url_input.text, token)


func _require_token() -> bool:
    if access_token.is_empty():
        _set_status("Register or login first.")
        return false
    return true


func _require_character() -> bool:
    if not _require_token():
        return false
    if character.is_empty() or not character.has("id"):
        _set_status("Create a character first.")
        return false
    return true


func _show_splash_screen() -> void:
    world_active = false
    touch_move = Vector2.ZERO
    splash_screen.visible = true
    auth_screen.visible = false
    character_screen.visible = false
    world_screen.visible = false
    _set_status("Welcome to Auralis.")


func _show_auth_screen() -> void:
    world_active = false
    touch_move = Vector2.ZERO
    splash_screen.visible = false
    auth_screen.visible = true
    character_screen.visible = false
    world_screen.visible = false


func _show_character_screen() -> void:
    world_active = false
    touch_move = Vector2.ZERO
    splash_screen.visible = false
    auth_screen.visible = false
    character_screen.visible = true
    world_screen.visible = false
    _refresh_character_lobby(status_label.text)


func _show_world_screen() -> void:
    splash_screen.visible = false
    auth_screen.visible = false
    character_screen.visible = false
    world_screen.visible = true
    world_active = true
    _update_interaction_prompt()


func _refresh_character_lobby(message: String) -> void:
    _set_status(message)
    if character_card == null or enter_world_button == null:
        return

    var has_character := not character.is_empty() and character.has("id")
    enter_world_button.visible = has_character
    if has_character:
        character_card.text = (
            "[b]Saved Wayfarer[/b]\n"
            + "Name: %s\nPeople: %s\nOrigin: %s\nLevel: %s\nXP: %s\nZone: %s\n\n"
            + "Progress is retained on the server. Press Enter World to continue."
        ) % [
            character.get("name", "-"),
            character.get("ancestry_key", "-"),
            character.get("origin_key", "-"),
            character.get("level", "-"),
            character.get("experience", "-"),
            character.get("current_zone_key", "-"),
        ]
    else:
        character_card.text = (
            "[b]No character found[/b]\n"
            + "Create your first Wayfarer. The art can be replaced later, but this flow "
            + "is the foundation for public account and character retention."
        )


func _open_dialogue_panel() -> void:
    _close_combat_panel()
    dialogue_panel.visible = true
    var quest_state := _starter_quest_state()
    if quest_state == "completed":
        dialogue_text.text = (
            "[b]Mara Lanternwright[/b]\n"
            + "\"The well is steady again. Dawnreef owes you a lantern kept burning.\"\n\n"
            + "Quest complete."
        )
        dialogue_accept_button.visible = false
    elif quest_state == "accepted":
        dialogue_text.text = (
            "[b]Mara Lanternwright[/b]\n"
            + "\"The fog-thorn lurker still nests by the reeds. Drive it away and return safe.\"\n\n"
            + "Quest in progress."
        )
        dialogue_accept_button.visible = false
    else:
        dialogue_text.text = (
            "[b]Mara Lanternwright[/b]\n"
            + "\"The Lantern Well is fading. If you can drive off the fog-thorn lurker, "
            + "Dawnreef gets one more safe night.\"\n\n"
            + "Quest: First Light at the Lantern Well"
        )
        dialogue_accept_button.visible = true
    _set_status("Talking with Mara.")


func _close_dialogue_panel() -> void:
    if dialogue_panel != null:
        dialogue_panel.visible = false


func _open_combat_panel() -> void:
    _close_dialogue_panel()
    combat_panel.visible = true
    if _starter_quest_state() == "completed":
        combat_text.text = (
            "[b]Fog-Thorn Lurker[/b]\n"
            + "This threat has already been pushed back. You can still test spells, "
            + "but the starter quest reward has already been claimed."
        )
    else:
        combat_text.text = (
            "[b]Fog-Thorn Lurker[/b]\n"
            + "Choose a spell.\n\n"
            + "Glimmer Spark: direct luminous strike.\n"
            + "Root Snare: reliable starter attack.\n"
            + "Tide Mend: restore vigor, then counterattack."
        )
    _set_status("Choose a combat action.")


func _close_combat_panel() -> void:
    if combat_panel != null:
        combat_panel.visible = false


func _show_character_state(message: String) -> void:
    _set_status(message)
    _refresh_hud()
    _set_event_log(_character_snapshot())


func _refresh_hud() -> void:
    profile_label.text = _profile_summary()
    quest_tracker_label.text = _quest_tracker_summary()
    minimap_label.text = _minimap_summary()
    character_summary.text = _character_summary()
    quest_summary.text = _quest_summary()
    inventory_summary.text = _inventory_summary()
    _refresh_world_feedback()


func _refresh_world_feedback() -> void:
    if enemy_marker != null:
        if _starter_quest_state() == "completed":
            enemy_marker.material_override = _material(Color(0.35, 0.35, 0.35))
        else:
            enemy_marker.material_override = _material(Color(0.8, 0.25, 0.25))


func _character_summary() -> String:
    return "[b]Character[/b]\nName: %s\nLevel: %s\nXP: %s\nZone: %s\nVigor: %s\nSpells: %s" % [
        character.get("name", "-"),
        character.get("level", "-"),
        character.get("experience", "-"),
        character.get("current_zone_key", "-"),
        character.get("vigor", "-"),
        _join_values(character.get("known_spells", []) as Array),
    ]


func _profile_summary() -> String:
    return "[b]%s[/b]\nLv %s Wayfarer\nHP %s/30  Energy 3/3\nXP %s" % [
        character.get("name", "Wayfarer"),
        character.get("level", "-"),
        character.get("vigor", "-"),
        character.get("experience", "-"),
    ]


func _quest_tracker_summary() -> String:
    var state := _starter_quest_state()
    var objective := "Talk to Mara"
    if state == "accepted":
        objective = "Defeat Fog-Thorn Lurker"
    elif state == "completed":
        objective = "Completed"
    return "[b]Tracked Quest[/b]\nFirst Light at the Lantern Well\n%s" % objective


func _minimap_summary() -> String:
    if player_marker == null:
        return "[b]Mini Map[/b]\nDawnreef"
    return "[b]Mini Map[/b]\nDawnreef Commons\nPlayer %.1f, %.1f\nZoom + / -" % [
        player_marker.position.x,
        player_marker.position.z,
    ]


func _quest_summary() -> String:
    var quests: Dictionary = character.get("quest_state", {}) as Dictionary
    if not quests.has(STARTER_QUEST_KEY):
        return "[b]Quest[/b]\nFirst Light at the Lantern Well: not accepted"
    var quest: Dictionary = quests[STARTER_QUEST_KEY] as Dictionary
    var objectives: Dictionary = quest.get("objectives", {}) as Dictionary
    return "[b]Quest[/b]\nFirst Light at the Lantern Well: %s\nDefeat Fog-Thorn Lurker: %s/1" % [
        quest.get("state", "unknown"),
        objectives.get("defeat_fog_thorn_lurker", 0),
    ]


func _starter_quest_state() -> String:
    var quests: Dictionary = character.get("quest_state", {}) as Dictionary
    if not quests.has(STARTER_QUEST_KEY):
        return "not_accepted"
    var quest: Dictionary = quests[STARTER_QUEST_KEY] as Dictionary
    return str(quest.get("state", "unknown"))


func _inventory_summary() -> String:
    return "[b]Inventory[/b]\nItems: %s\nWallet: %s\nDefeated: %s" % [
        _format_dict(character.get("inventory", {}) as Dictionary),
        _format_dict(character.get("wallet", {}) as Dictionary),
        _format_dict(character.get("defeated_enemies", {}) as Dictionary),
    ]


func _character_snapshot() -> String:
    return "Name: %s\nLevel: %s\nXP: %s\nQuest: %s\nInventory: %s\nWallet: %s" % [
        character.get("name", "-"),
        character.get("level", "-"),
        character.get("experience", "-"),
        character.get("quest_state", {}),
        character.get("inventory", {}),
        character.get("wallet", {}),
    ]


func _fight_summary(response: Dictionary) -> String:
    return "Victory: %s\nXP gained: %s\nLevel gained: %s\nQuest completed: %s\nRewards: %s" % [
        response.get("victory", false),
        response.get("experience_gained", 0),
        response.get("level_gained", false),
        response.get("quest_completed", "-"),
        response.get("rewards", {}),
    ]


func _spell_name(spell_key: String) -> String:
    match spell_key:
        SPELL_GLIMMER_SPARK:
            return "Glimmer Spark"
        SPELL_ROOT_SNARE:
            return "Root Snare"
        SPELL_TIDE_MEND:
            return "Tide Mend"
        _:
            return spell_key


func _pulse_enemy_marker() -> void:
    if enemy_marker == null:
        return
    var original_scale := enemy_marker.scale
    enemy_marker.scale = original_scale * 1.35
    await get_tree().create_timer(0.16).timeout
    if enemy_marker != null:
        enemy_marker.scale = original_scale


func _format_dict(value: Dictionary) -> String:
    if value.is_empty():
        return "-"
    var parts: Array[String] = []
    for key in value.keys():
        parts.append("%s x%s" % [key, value[key]])
    return _join_values(parts)


func _focus_travel_gate() -> void:
    if player_marker != null:
        player_marker.position = TRAVEL_GATE_POSITION + Vector3(0, 0.2, -1.0)
        camera.position.x = player_marker.position.x
        camera.position.z = player_marker.position.z + 9.0
        _update_interaction_prompt()
    _set_event_log("[b]Travel Gate[/b]\nThe gate is visible from the commons. Full region travel is planned for multiplayer expansion.")


func _show_stub_menu() -> void:
    if secondary_tray != null:
        secondary_tray.visible = not secondary_tray.visible
    _set_event_log("[b]Menu[/b]\nInventory, Character, Collections, Mounts, Friends, Mail, Settings, and Nearby are stubbed for future MMO systems.")


func _join_values(values: Array) -> String:
    if values.is_empty():
        return "-"
    var text_values: Array[String] = []
    for value in values:
        text_values.append(str(value))
    return ", ".join(text_values)


func _set_event_log(message: String) -> void:
    event_log.text = "[b]Latest Event[/b]\n%s" % message


func _set_status(message: String) -> void:
    status_label.text = message


func _on_request_failed(endpoint: String, status_code: int, message: String) -> void:
    _set_status("Request failed: %s (%s)" % [endpoint, status_code])
    _set_event_log(message)
