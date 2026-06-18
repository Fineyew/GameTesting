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

var root: VBoxContainer
var auth_screen: VBoxContainer
var character_screen: VBoxContainer
var world_screen: HSplitContainer
var player_marker: MeshInstance3D
var enemy_marker: MeshInstance3D
var camera: Camera3D
var api_url_input: LineEdit
var email_input: LineEdit
var password_input: LineEdit
var display_name_input: LineEdit
var character_name_input: LineEdit
var status_label: Label
var interaction_label: Label
var talk_button: Button
var fight_button: Button
var dialogue_accept_button: Button
var dialogue_panel: PanelContainer
var dialogue_text: RichTextLabel
var combat_panel: PanelContainer
var combat_text: RichTextLabel
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
    root.offset_left = 24
    root.offset_top = 24
    root.offset_right = -24
    root.offset_bottom = -24
    root.add_theme_constant_override("separation", 10)
    add_child(root)

    var title := Label.new()
    title.text = "Veilbound Tides - Dawnreef Atoll"
    title.add_theme_font_size_override("font_size", 28)
    title.add_theme_color_override("font_color", COLOR_GOLD)
    root.add_child(title)

    status_label = Label.new()
    status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    status_label.add_theme_color_override("font_color", COLOR_TEXT)
    root.add_child(status_label)

    _build_auth_screen()
    _build_character_screen()
    _build_world_screen()
    _show_auth_screen()


func _build_auth_screen() -> void:
    auth_screen = VBoxContainer.new()
    auth_screen.add_theme_constant_override("separation", 10)
    root.add_child(auth_screen)

    var description := Label.new()
    description.text = "Connect to the deployed backend, then register or login."
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

    var description := Label.new()
    description.text = "Create the first playable character for this account."
    description.add_theme_color_override("font_color", COLOR_TEXT)
    character_screen.add_child(description)

    character_name_input = _line_edit("Ari%s" % Time.get_unix_time_from_system(), "Character name")
    character_screen.add_child(_labeled_row("Character", character_name_input))

    character_screen.add_child(_button_row([
        ["Create Character", Callable(self, "_on_create_character_pressed")],
        ["Logout", Callable(self, "_on_logout_pressed")],
    ]))


func _build_world_screen() -> void:
    world_screen = HSplitContainer.new()
    world_screen.size_flags_vertical = Control.SIZE_EXPAND_FILL
    root.add_child(world_screen)

    var viewport_container := SubViewportContainer.new()
    viewport_container.stretch = true
    viewport_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    viewport_container.size_flags_vertical = Control.SIZE_EXPAND_FILL
    viewport_container.add_theme_stylebox_override("panel", _style_box(Color(0.05, 0.07, 0.12), 10))
    world_screen.add_child(viewport_container)

    var viewport := SubViewport.new()
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    viewport_container.add_child(viewport)
    _build_placeholder_world(viewport)

    var hud := VBoxContainer.new()
    hud.custom_minimum_size = Vector2(420, 0)
    hud.add_theme_constant_override("separation", 10)
    world_screen.add_child(hud)

    var hud_title := Label.new()
    hud_title.text = "Dawnreef Field HUD"
    hud_title.add_theme_font_size_override("font_size", 22)
    hud_title.add_theme_color_override("font_color", COLOR_GOLD)
    hud.add_child(hud_title)

    interaction_label = Label.new()
    interaction_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    interaction_label.add_theme_color_override("font_color", COLOR_TEXT)
    hud.add_child(interaction_label)

    character_summary = _rich_panel()
    quest_summary = _rich_panel()
    inventory_summary = _rich_panel()
    event_log = _rich_panel()
    event_log.size_flags_vertical = Control.SIZE_EXPAND_FILL

    hud.add_child(character_summary)
    hud.add_child(quest_summary)
    hud.add_child(inventory_summary)

    var movement_hint := Label.new()
    movement_hint.text = "Move: WASD, arrow keys, or the on-screen controls."
    movement_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    movement_hint.add_theme_color_override("font_color", COLOR_TEXT)
    hud.add_child(movement_hint)

    hud.add_child(_movement_pad())

    var action_row := _button_row([
        ["Refresh World", Callable(self, "_on_enter_world_pressed")],
        ["Save", Callable(self, "_on_save_pressed")],
        ["Logout", Callable(self, "_on_logout_pressed")],
    ])
    hud.add_child(action_row)

    talk_button = Button.new()
    talk_button.text = "Talk to Mara"
    talk_button.pressed.connect(Callable(self, "_open_dialogue_panel"))
    hud.add_child(talk_button)

    fight_button = Button.new()
    fight_button.text = "Fight Fog-Thorn"
    fight_button.pressed.connect(Callable(self, "_open_combat_panel"))
    hud.add_child(fight_button)

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
    plane.size = Vector2(12, 12)
    ground.mesh = plane
    ground.material_override = _material(Color(0.24, 0.45, 0.34))
    world.add_child(ground)

    _add_box_prop(world, "Glimmerdeep Water", Vector3(0, -0.04, 0), Vector3(13.0, 0.04, 13.0), Color(0.05, 0.20, 0.32))
    _add_box_prop(world, "Dawnreef Walkway", Vector3(0, 0.02, -1.65), Vector3(7.2, 0.05, 0.8), Color(0.78, 0.64, 0.42))
    _add_box_prop(world, "Lantern Well Base", Vector3(0, 0.18, -1.65), Vector3(1.2, 0.34, 1.2), Color(0.32, 0.30, 0.38))
    _add_box_prop(world, "Lantern Well Light", Vector3(0, 0.85, -1.65), Vector3(0.42, 0.9, 0.42), Color(1.0, 0.78, 0.25))

    for offset in [-4.8, -4.1, 4.1, 4.8]:
        _add_box_prop(world, "Sunthread Reeds", Vector3(offset, 0.35, 1.7), Vector3(0.16, 0.7, 0.16), Color(0.86, 0.68, 0.30))

    _add_box_prop(world, "Blue Veil Crystal", Vector3(-2.2, 0.55, 2.4), Vector3(0.32, 1.1, 0.32), Color(0.32, 0.75, 1.0))
    _add_box_prop(world, "Violet Veil Crystal", Vector3(2.2, 0.45, 2.1), Vector3(0.28, 0.9, 0.28), Color(0.72, 0.44, 1.0))

    player_marker = _add_marker(world, "Player", Vector3(0, 0.7, 0), Color(0.3, 0.65, 1.0), CapsuleMesh.new())
    _add_marker(world, "Mara NPC", NPC_POSITION, Color(1.0, 0.78, 0.25), SphereMesh.new())
    enemy_marker = _add_marker(world, "Fog-Thorn Enemy", ENEMY_POSITION, Color(0.8, 0.25, 0.25), BoxMesh.new())
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
        _style_button(button)
        button.pressed.connect(button_data[1])
        row.add_child(button)
    return row


func _style_button(button: Button) -> void:
    button.add_theme_stylebox_override("normal", _style_box(COLOR_BUTTON, 8))
    button.add_theme_stylebox_override("hover", _style_box(COLOR_BUTTON_HOVER, 8))
    button.add_theme_stylebox_override("pressed", _style_box(Color(0.18, 0.16, 0.28), 8))
    button.add_theme_color_override("font_color", COLOR_TEXT)
    button.add_theme_color_override("font_hover_color", Color.WHITE)


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


func _movement_pad() -> GridContainer:
    var pad := GridContainer.new()
    pad.columns = 3

    pad.add_child(_pad_spacer())
    pad.add_child(_movement_button("Up", Vector2(0, -1)))
    pad.add_child(_pad_spacer())
    pad.add_child(_movement_button("Left", Vector2(-1, 0)))
    pad.add_child(_pad_spacer())
    pad.add_child(_movement_button("Right", Vector2(1, 0)))
    pad.add_child(_pad_spacer())
    pad.add_child(_movement_button("Down", Vector2(0, 1)))
    pad.add_child(_pad_spacer())
    return pad


func _movement_button(label_text: String, direction: Vector2) -> Button:
    var button := Button.new()
    button.text = label_text
    button.custom_minimum_size = Vector2(84, 42)
    _style_button(button)
    button.button_down.connect(func() -> void:
        touch_move = _clamp_touch_move(touch_move + direction)
    )
    button.button_up.connect(func() -> void:
        touch_move = _clamp_touch_move(touch_move - direction)
    )
    return button


func _pad_spacer() -> Control:
    var spacer := Control.new()
    spacer.custom_minimum_size = Vector2(84, 42)
    return spacer


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
    player_marker.position.x = clamp(player_marker.position.x, -5.5, 5.5)
    player_marker.position.z = clamp(player_marker.position.z, -5.5, 5.5)
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
    })
    if response.is_empty():
        return
    character = response
    _show_world_screen()
    _show_character_state("Character created.")


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
            await _on_enter_world_pressed()
            return
    _show_character_screen()
    _set_status("%s Create a character to enter Dawnreef." % message)


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


func _show_auth_screen() -> void:
    world_active = false
    touch_move = Vector2.ZERO
    auth_screen.visible = true
    character_screen.visible = false
    world_screen.visible = false


func _show_character_screen() -> void:
    world_active = false
    touch_move = Vector2.ZERO
    auth_screen.visible = false
    character_screen.visible = true
    world_screen.visible = false


func _show_world_screen() -> void:
    auth_screen.visible = false
    character_screen.visible = false
    world_screen.visible = true
    world_active = true
    _update_interaction_prompt()


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
