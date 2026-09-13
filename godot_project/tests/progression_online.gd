extends SceneTree
## Continues the character genuinely earned by online.gd in the same isolated server.
## No save fixture, debug grant, position teleport or direct rule injection.
func _init() -> void:
    call_deferred("run")

func until(check: Callable, seconds := 12.0) -> void:
    var elapsed := 0.0
    while not check.call() and elapsed < seconds:
        await create_timer(.1).timeout
        elapsed += .1
    assert(check.call(),"progression online condition timed out")

func walk(session: Node, target: Vector2) -> void:
    session.hud.close_panel()
    var elapsed := 0.0
    while Vector2(session.player.position.x,session.player.position.z).distance_to(target) > .25 and elapsed < 12:
        var offset = target-Vector2(session.player.position.x,session.player.position.z)
        session.hud.stick.axis = (offset*1.2).limit_length()
        await create_timer(.1).timeout
        elapsed += .1
    session.hud.stick.release()
    assert(elapsed < 12,"progression navigation timed out: "+str(target))
    await create_timer(.35).timeout

func prepare(session: Node, keys: Array) -> void:
    await session.show_folio()
    for key in session.folio_panel.selected.duplicate():
        if key not in keys:
            session.folio_panel.choices[key].pressed.emit()
    for key in keys:
        if key not in session.folio_panel.selected:
            session.folio_panel.choices[key].pressed.emit()
    if session.folio_panel.selected != session.folio_panel.saved:
        session.folio_panel.save_button.pressed.emit()
        await until(func(): return not session.busy)
    assert(session.character.folio.size() == keys.size() and keys.all(func(key): return key in session.character.folio))
    session.hud.close_panel()

func heal(session: Node, minimum: int) -> void:
    while int(session.character.vigor) < minimum:
        await session.show_inventory()
        if int(session.character.inventory.get("sunthread_bandage",0)) == 0:
            var balance = int(session.character.wallet.shell_chits)
            assert(balance >= 5,"Practice must be affordable with earned currency")
            await session.show_vendor()
            session.commerce_panel.buy_buttons.buy_sunthread_bandage.pressed.emit()
            await until(func(): return not session.busy)
            assert(int(session.character.wallet.shell_chits) == balance-5)
            await session.show_inventory()
        assert(int(session.character.inventory.get("sunthread_bandage",0)) > 0)
        session.commerce_panel.use_buttons.sunthread_bandage.pressed.emit()
        await until(func(): return not session.busy)
    session.hud.close_panel()

func fight(session: Node, enemy_key: String, actions: Array) -> void:
    await session.start_encounter(enemy_key)
    assert(session.character.encounter.enemy_key == enemy_key and session.character.encounter.state == "active")
    assert(session.world.enemy == session.world.enemies[enemy_key],"Intent/effect target must follow the server enemy")
    for action in actions:
        assert(session.character.encounter.state == "active","Route must not issue an action after victory")
        var beat = int(session.character.encounter.round)
        session.cast(action)
        await until(func(): return not session.busy)
        assert(int(session.character.encounter.round) == beat+1 and session.pending_action.is_empty())
        if action == "stillwater_knot" and beat == 1:
            assert(int(session.character.encounter.last_focus_loss) == 0)
    assert(session.character.encounter.state == "victory")
    var saved = await root.get_node("ApiClient").get_json("/world/characters/"+session.character.id)
    assert(saved.encounter == session.character.encounter and saved.experience == session.character.experience)
    session.hud.close_panel()

func lesson(session: Node, key: String) -> void:
    await session.open_dialogue()
    assert(session.dialogue.options.any(func(option): return option.key == "study_"+key))
    await session.choose_dialogue("study_"+key)
    assert(session.character.quest_state.has(key))
    session.hud.close_panel()

func claim(session: Node, quest: String, spell: String) -> void:
    await session.open_dialogue()
    assert(session.character.quest_state[quest].rewards_claimed and spell in session.character.known_spells)
    assert(spell not in session.character.folio,"Earned spell must not replace a prepared slot")
    var xp = session.character.experience
    await session.open_dialogue()
    assert(session.character.experience == xp)
    session.hud.close_panel()

func run() -> void:
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    await create_timer(.2).timeout
    app.server_url = OS.get_environment("VT_TEST_API_URL")
    app.email.text = "godot@example.test"
    app.password.text = "development-only-password"
    await app.authenticate(false)
    assert(not app.selected_character.is_empty())
    await app.enter_world()
    var session = app.session
    await until(func(): return session.online_ready())
    assert(session.character.known_spells.size() == 6 and session.character.experience == 190)
    var identity = session.character.id
    var appearance = session.character.appearance.duplicate(true)
    session.short_spell_effects = true
    await walk(session,Vector2(6,9))
    await walk(session,Vector2(0,4))
    await walk(session,Vector2(-4,-4))
    await lesson(session,"light_between_plates")
    await prepare(session,["glimmer_spark","root_snare","tide_mend","beacon_trace","reed_aegis","seam_lance"])
    await heal(session,28)
    await walk(session,Vector2(-4,7))
    await fight(session,"shellfold_sifter",["beacon_trace","glimmer_spark","tide_mend","glimmer_spark","glimmer_spark","tide_mend","beacon_trace","glimmer_spark"])
    assert(session.character.level == 3 and session.character.experience == 225)
    await walk(session,Vector2(-4,-4))
    await claim(session,"light_between_plates","prism_needle")
    await lesson(session,"keep_the_quiet")
    await heal(session,28)
    await walk(session,Vector2(0,-4))
    await walk(session,Vector2(14,-2))
    await fight(session,"hushfin_ray",["beacon_trace","glimmer_spark","gather","tide_mend","glimmer_spark","glimmer_spark"])
    await walk(session,Vector2(0,-4))
    await walk(session,Vector2(-4,-4))
    await claim(session,"keep_the_quiet","stillwater_knot")
    await lesson(session,"a_kindly_weave")
    await prepare(session,["glimmer_spark","prism_needle","tide_mend","beacon_trace","reed_aegis","seam_lance"])
    await heal(session,28)
    await walk(session,Vector2(-4,7))
    await fight(session,"shellfold_sifter",["gather","reed_aegis","tide_mend","beacon_trace","seam_lance","gather","glimmer_spark","prism_needle","glimmer_spark"])
    await walk(session,Vector2(-4,-4))
    await claim(session,"a_kindly_weave","reed_stitch")
    await prepare(session,["glimmer_spark","prism_needle","tide_mend","beacon_trace","reed_stitch","stillwater_knot"])
    await heal(session,24)
    await walk(session,Vector2(0,-4))
    await walk(session,Vector2(14,-2))
    await fight(session,"hushfin_ray",["stillwater_knot","reed_stitch","gather","prism_needle","glimmer_spark","glimmer_spark"])
    for key in ["prism_needle","reed_stitch","stillwater_knot"]:
        assert(session.playback.presented.get(key,0) > 0)
    session.connection.socket.close()
    await until(func(): return not session.connection.connected)
    await until(func(): return session.online_ready())
    await session.show_folio()
    assert(session.character.id == identity and session.character.appearance == appearance)
    assert(session.character.known_spells.size() == 9 and session.character.folio.size() == 6)
    assert(session.character.experience == 405 and session.character.level == 5)
    assert("XP 405 / 500" in session.hud.progression_label.text)
    app.return_to_gateway()
    await root.get_node("ApiClient").post_json("/auth/logout",{})
    app.queue_free()
    await process_frame
    print("GODOT_PROGRESSION_PASS: ordinary earned-save continuation, two enemies, affinity/cross-training, three lessons/spells, six-slot GUI folio, supplies, XP, real presentation and reconnect")
    await root.get_node("Soundscape").shutdown()
    quit.call_deferred()
