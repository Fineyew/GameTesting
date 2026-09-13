extends SceneTree
## Deterministic offline effect review, never a live combat grant or phone FPS claim.
func _init() -> void:
    call_deferred("run")

func run() -> void:
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    await create_timer(.3).timeout
    app.start_preview()
    var session = app.session
    session.player.position = Vector3(10,0,-8)
    session.camera.follow(session.player)
    session.busy = true
    session.short_spell_effects = false
    session.reduced_motion = false
    var sound = root.get_node("Soundscape")
    sound.set_combat(true)
    var before = TidebeatChecks.fixture()
    before.enemy_name = "Fog-thorn Lurker · effect review"
    await create_timer(.5).timeout
    for key in TidebeatEffect.PROFILES:
        var authored = TidebeatChecks.fixture(key)
        session.world.show_intent(authored)
        session.player.position = session.world.enemy.position+Vector3(-2,0,2)
        session.camera.follow(session.player)
        await session.playback.play(key,authored,TidebeatChecks.outcome(key),"movie-"+key)
        await create_timer(.15).timeout
    session.reduced_motion = true
    await session.playback.play("reed_aegis",before,TidebeatChecks.outcome("reed_aegis"),"movie-reduced")
    session.short_spell_effects = true
    await session.playback.play("glimmer_spark",before,TidebeatChecks.outcome("glimmer_spark"),"movie-short")
    app.queue_free()
    await process_frame
    print("TIDEBEAT_ROUTE_PASS")
    await sound.shutdown()
    quit.call_deferred()
