extends SceneTree

func _init() -> void:
    call_deferred("run")

func until(check: Callable, seconds := 12.0) -> void:
    var elapsed := 0.0
    while not check.call() and elapsed < seconds:
        await create_timer(.1).timeout
        elapsed += .1
    assert(check.call(),"online condition timed out")

func walk(session, target: Vector2) -> void:
    var elapsed := 0.0
    while Vector2(session.player.position.x,session.player.position.z).distance_to(target) > .3 and elapsed < 12:
        session.hud.stick.axis = (target-Vector2(session.player.position.x,session.player.position.z)).normalized()
        await create_timer(.1).timeout
        elapsed += .1
    session.hud.stick.release()
    assert(elapsed < 12,"navigation timed out")
    await create_timer(.5).timeout

func run() -> void:
    var api = root.get_node("ApiClient")
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    await create_timer(.2).timeout
    app.server_url = OS.get_environment("VT_TEST_API_URL")
    app.email.text = "godot@example.test"
    app.password.text = "development-only-password"
    app.display_name.text = "Godot tester"
    await app.authenticate(true)
    assert(not api.access_token.is_empty(),"registration failed")
    await app.create_character("Reef Tester",0,0,0)
    assert(not app.selected_character.is_empty(),"creation failed")
    await app.enter_world()
    var session = app.session
    assert(session != null,"world did not open")
    await until(func(): return session.connection.connected and session.remotes.size() == 1)
    await session.accept_quest()
    await walk(session,Vector2(0,-10))
    await walk(session,Vector2(10,-10))
    await session.start_encounter()
    assert(session.character.encounter.state == "active","server proximity rejected encounter")
    for beat in 4:
        session.cast("glimmer_spark")
        await until(func(): return not session.busy)
    assert(session.character.encounter.state == "victory","combat did not resolve")
    assert(session.character.wallet.shell_chits == 14,"reward mismatch")
    var identity = session.character.id
    session.hud.close_panel()
    session.connection.socket.close()
    await until(func(): return not session.connection.connected)
    await until(func(): return session.connection.connected)
    var saved = await api.get_json("/world/characters/" + identity)
    assert(saved.wallet.shell_chits == 14,"reconnect changed reward")
    app.return_to_gateway()
    await api.post_json("/auth/logout",{})
    app.queue_free()
    await process_frame
    print("GODOT_ONLINE_PASS: account, creation, two-player presence, movement, quest, combat, rewards, reconnect")
    quit()
