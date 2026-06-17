extends Control

const DEFAULT_API_URL := "https://game.surveyroute.work/api/v1"
const STARTER_QUEST_KEY := "lantern_well_first_light"
const STARTER_ENEMY_KEY := "fog_thorn_lurker"
const STARTER_SPELL_KEY := "root_snare"

var account := {}
var character := {}
var access_token := ""

var root: VBoxContainer
var auth_screen: VBoxContainer
var character_screen: VBoxContainer
var world_screen: HSplitContainer
var api_url_input: LineEdit
var email_input: LineEdit
var password_input: LineEdit
var display_name_input: LineEdit
var character_name_input: LineEdit
var status_label: Label
var character_summary: RichTextLabel
var quest_summary: RichTextLabel
var inventory_summary: RichTextLabel
var event_log: RichTextLabel


func _ready() -> void:
    ApiClient.request_failed.connect(_on_request_failed)
    _build_ui()
    _set_status("Ready. Register or login to begin.")


func _build_ui() -> void:
    root = VBoxContainer.new()
    root.set_anchors_preset(Control.PRESET_FULL_RECT)
    root.offset_left = 24
    root.offset_top = 24
    root.offset_right = -24
    root.offset_bottom = -24
    root.add_theme_constant_override("separation", 10)
    add_child(root)

    var title := Label.new()
    title.text = "Veilbound Tides - Vertical Slice Client"
    title.add_theme_font_size_override("font_size", 28)
    root.add_child(title)

    status_label = Label.new()
    status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
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
    hud.add_child(hud_title)

    character_summary = _rich_panel()
    quest_summary = _rich_panel()
    inventory_summary = _rich_panel()
    event_log = _rich_panel()
    event_log.size_flags_vertical = Control.SIZE_EXPAND_FILL

    hud.add_child(character_summary)
    hud.add_child(quest_summary)
    hud.add_child(inventory_summary)

    hud.add_child(_button_row([
        ["Refresh World", Callable(self, "_on_enter_world_pressed")],
        ["Accept Quest", Callable(self, "_on_accept_quest_pressed")],
        ["Fight Enemy", Callable(self, "_on_fight_enemy_pressed")],
        ["Save", Callable(self, "_on_save_pressed")],
        ["Logout", Callable(self, "_on_logout_pressed")],
    ]))

    hud.add_child(event_log)


func _build_placeholder_world(viewport: SubViewport) -> void:
    var world := Node3D.new()
    viewport.add_child(world)

    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-55, 35, 0)
    light.light_energy = 2.0
    world.add_child(light)

    var camera := Camera3D.new()
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

    _add_marker(world, "Player", Vector3(0, 0.7, 0), Color(0.3, 0.65, 1.0), CapsuleMesh.new())
    _add_marker(world, "Mara NPC", Vector3(-3, 0.5, -1.6), Color(1.0, 0.78, 0.25), SphereMesh.new())
    _add_marker(world, "Fog-Thorn Enemy", Vector3(3, 0.5, -1.8), Color(0.8, 0.25, 0.25), BoxMesh.new())


func _add_marker(world: Node3D, label_text: String, position: Vector3, color: Color, mesh: Mesh) -> void:
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
    return input


func _labeled_row(label_text: String, input: Control) -> HBoxContainer:
    var row := HBoxContainer.new()
    var label := Label.new()
    label.text = label_text
    label.custom_minimum_size = Vector2(110, 0)
    row.add_child(label)
    row.add_child(input)
    return row


func _button_row(buttons: Array) -> HBoxContainer:
    var row := HBoxContainer.new()
    row.add_theme_constant_override("separation", 8)
    for button_data in buttons:
        var button := Button.new()
        button.text = button_data[0]
        button.pressed.connect(button_data[1])
        row.add_child(button)
    return row


func _rich_panel() -> RichTextLabel:
    var panel := RichTextLabel.new()
    panel.bbcode_enabled = true
    panel.fit_content = true
    panel.scroll_active = true
    panel.custom_minimum_size = Vector2(0, 90)
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
    var response := await ApiClient.post_json(
        "/world/characters/%s/quests/%s/accept" % [character["id"], STARTER_QUEST_KEY],
        {}
    )
    if response.is_empty():
        return
    character = response
    _show_character_state("Quest accepted.")


func _on_fight_enemy_pressed() -> void:
    if not _require_character():
        return
    _set_status("Fighting enemy...")
    var response := await ApiClient.post_json(
        "/world/characters/%s/combat/fight" % character["id"],
        {
            "enemy_key": STARTER_ENEMY_KEY,
            "spell_key": STARTER_SPELL_KEY,
        }
    )
    if response.is_empty():
        return
    if response.has("character"):
        character = response["character"]
    _show_character_state("Fight complete.")
    _set_event_log(_fight_summary(response))


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
    auth_screen.visible = true
    character_screen.visible = false
    world_screen.visible = false


func _show_character_screen() -> void:
    auth_screen.visible = false
    character_screen.visible = true
    world_screen.visible = false


func _show_world_screen() -> void:
    auth_screen.visible = false
    character_screen.visible = false
    world_screen.visible = true


func _show_character_state(message: String) -> void:
    _set_status(message)
    _refresh_hud()
    _set_event_log(_character_snapshot())


func _refresh_hud() -> void:
    character_summary.text = _character_summary()
    quest_summary.text = _quest_summary()
    inventory_summary.text = _inventory_summary()


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
