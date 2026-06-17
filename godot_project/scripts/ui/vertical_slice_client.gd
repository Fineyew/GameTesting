extends Control

const DEFAULT_API_URL := "https://game.surveyroute.work/api/v1"
const STARTER_QUEST_KEY := "lantern_well_first_light"
const STARTER_ENEMY_KEY := "fog_thorn_lurker"
const STARTER_SPELL_KEY := "root_snare"

var account := {}
var character := {}
var access_token := ""

var api_url_input: LineEdit
var email_input: LineEdit
var password_input: LineEdit
var display_name_input: LineEdit
var character_name_input: LineEdit
var status_label: Label
var output: TextEdit


func _ready() -> void:
    ApiClient.request_failed.connect(_on_request_failed)
    _build_ui()
    _set_status("Ready. Register or login to begin.")


func _build_ui() -> void:
    var root := VBoxContainer.new()
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

    api_url_input = _line_edit(DEFAULT_API_URL, "API base URL")
    root.add_child(_labeled_row("API", api_url_input))

    email_input = _line_edit("player%s@example.com" % Time.get_unix_time_from_system(), "Email")
    root.add_child(_labeled_row("Email", email_input))

    password_input = _line_edit("safe-password", "Password")
    password_input.secret = true
    root.add_child(_labeled_row("Password", password_input))

    display_name_input = _line_edit("Player%s" % Time.get_unix_time_from_system(), "Display name")
    root.add_child(_labeled_row("Display", display_name_input))

    character_name_input = _line_edit("Ari%s" % Time.get_unix_time_from_system(), "Character name")
    root.add_child(_labeled_row("Character", character_name_input))

    root.add_child(_button_row([
        ["Register", Callable(self, "_on_register_pressed")],
        ["Login", Callable(self, "_on_login_pressed")],
        ["Create Character", Callable(self, "_on_create_character_pressed")],
        ["Enter World", Callable(self, "_on_enter_world_pressed")],
    ]))

    root.add_child(_button_row([
        ["Accept Quest", Callable(self, "_on_accept_quest_pressed")],
        ["Fight Enemy", Callable(self, "_on_fight_enemy_pressed")],
        ["Save", Callable(self, "_on_save_pressed")],
        ["Logout", Callable(self, "_on_logout_pressed")],
    ]))

    output = TextEdit.new()
    output.editable = false
    output.wrap_mode = TextEdit.LINE_WRAPPING_BOUNDARY
    output.size_flags_vertical = Control.SIZE_EXPAND_FILL
    root.add_child(output)


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
    _show_state("Character created.", character)


func _on_enter_world_pressed() -> void:
    if not _require_character():
        return
    _set_status("Entering world...")
    var response := await ApiClient.get_json("/world/characters/%s" % character["id"])
    if response.is_empty():
        return
    character = response
    _show_state("Entered world.", character)


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
    _show_state("Quest accepted.", character)


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
    _show_state("Fight complete.", response)


func _on_save_pressed() -> void:
    if not _require_character():
        return
    _set_status("Saving progress...")
    var response := await ApiClient.post_json("/world/characters/%s/save" % character["id"], {})
    if response.is_empty():
        return
    character = response
    _show_state("Progress saved.", character)


func _on_logout_pressed() -> void:
    if not _require_token():
        return
    _set_status("Logging out...")
    var response := await ApiClient.post_json("/auth/logout", {})
    access_token = ""
    ApiClient.set_session(api_url_input.text, "")
    _show_state("Logged out.", response)


func _handle_auth_response(response: Dictionary, message: String) -> void:
    if response.is_empty():
        return
    account = response.get("account", {})
    access_token = response.get("access_token", "")
    _configure_api(access_token)
    _show_state(message, response)


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


func _show_state(message: String, data: Dictionary) -> void:
    _set_status(message)
    output.text = JSON.stringify(data, "\t")


func _set_status(message: String) -> void:
    status_label.text = message


func _on_request_failed(endpoint: String, status_code: int, message: String) -> void:
    _set_status("Request failed: %s (%s)" % [endpoint, status_code])
    output.text = message
