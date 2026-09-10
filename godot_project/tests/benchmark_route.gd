extends SceneTree
## Same read-only route runs against M1.3 and M1.4. Never interpret movie FPS as performance.
func _init() -> void:
    call_deferred("run")

func pause(seconds: float) -> void:
    await create_timer(seconds).timeout

func walk(session: Node, target: Vector2) -> void:
    var elapsed := 0.0
    while Vector2(session.player.position.x,session.player.position.z).distance_to(target) > .25 and elapsed < 8:
        var axis = (target-Vector2(session.player.position.x,session.player.position.z)).normalized()
        session.hud.stick.axis = axis.rotated(session.camera.yaw)
        await pause(.1)
        elapsed += .1
    session.hud.stick.release()
    assert(elapsed < 8,"Benchmark route hit an unexpected obstruction")
    await pause(.4)

func run() -> void:
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    app.world.sun.shadow_enabled = false
    root.scaling_3d_scale = .75
    Engine.max_fps = 30
    await pause(1.5)
    app.start_preview()
    var session = app.session
    await pause(.5)
    await walk(session,Vector2(0,-.5))
    await pause(2)
    await walk(session,Vector2(-4,-3))
    session.interact()
    await pause(2.5)
    session.hud.close_panel()
    session.camera.yaw = 1.0
    await pause(2)
    await walk(session,Vector2(-8,-2.5))
    await pause(2)
    session.camera.recenter()
    await walk(session,Vector2(0,-2))
    await pause(2)
    await walk(session,Vector2(3,-8))
    session.camera.yaw = PI
    await pause(2.5)
    session.camera.recenter()
    await walk(session,Vector2(10,-9))
    session.camera.yaw = -PI/2
    await pause(2)
    session.interact()
    await pause(2)
    session.hud.close_panel()
    await pause(1)
    app.queue_free()
    await process_frame
    print("BENCHMARK_ROUTE_PASS: preview only; identical camera, controls and .75/no-shadow preset")
    quit()
