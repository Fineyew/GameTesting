extends "res://tests/online.gd"

func run() -> void:
    var api = root.get_node("ApiClient")
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    app.server_url = OS.get_environment("VT_TEST_API_URL")
    app.email.text = "authoring@example.test"
    app.password.text = "isolated-authoring-password"
    app.display_name.text = "Author"
    await app.authenticate(true)
    assert(not api.access_token.is_empty())
    await app.create_character("Echo Listener",0,0,0)
    await app.enter_world()
    var session = app.session
    await until(func(): return session.connection.connected)
    assert(GameData.definition("quests","authoring_echo").display.name == "A Small Echo")
    await walk(session,Vector2(-4,-3))
    await session.open_dialogue()
    assert(session.dialogue.node == "authoring_echo")
    await session.choose_dialogue("listen")
    assert(session.character.quest_state.authoring_echo.state == "accepted")
    var experience = int(session.character.experience)
    session.hud.close_panel()
    await walk(session,Vector2(-9,-14))
    await session.inspect_landmark("sunthread_reeds")
    assert(not session.character.quest_state.authoring_echo.completed)
    session.hud.close_panel()
    await walk(session,Vector2(-4,-3))
    await session.open_dialogue()
    assert(session.character.quest_state.authoring_echo.completed)
    assert(int(session.character.experience) == experience+5)
    assert(session.dialogue.node != "authoring_echo")
    await session.open_dialogue()
    assert(int(session.character.experience) == experience+5)
    var saved = await api.get_json("/world/characters/"+session.character.id)
    assert(saved.quest_state.authoring_echo.completed)
    assert(int(saved.experience) == experience+5)
    app.return_to_gateway()
    await api.post_json("/auth/logout",{})
    app.queue_free()
    await process_frame
    print("GODOT_AUTHORING_PASS: generated catalog, branching offer, observed landmark/talk objectives, once-only reward and saved state")
    quit()
