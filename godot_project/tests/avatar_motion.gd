extends SceneTree
## Real imported rig and presentation calls. No account state or gameplay grants.

func _init() -> void:
    call_deferred("run")

func actor() -> WayfarerAvatar:
    var result = WayfarerAvatar.new()
    root.add_child(result)
    result.build({"robe":"teal","skin":"warm"})
    result.set_process(false)
    return result

func tick(avatar: WayfarerAvatar, delta: float) -> void:
    avatar._process(delta)
    avatar.animation.advance(delta)

func run() -> void:
    var avatar = actor()
    avatar.set_travel_velocity(Vector3(0,3,0))
    tick(avatar,1.0/60)
    assert(not avatar.walking and avatar.travel_speed == 0,
        "Vertical correction alone must not start a walk")
    assert(avatar.animation.current_animation == "Idle")
    avatar.set_travel_velocity(Vector3(2,3,0))
    tick(avatar,1.0/60)
    assert(avatar.walking and is_equal_approx(avatar.travel_speed,2),
        "Stair altitude must not increase gait speed")
    assert(avatar.animation.current_animation == "Walk")

    # A slow mover continues walking through small speed variations; a resting
    # avatar ignores the same jitter until it crosses the start threshold.
    for speed in [.14,.12,.09,.16]:
        avatar.set_travel_velocity(Vector3(speed,0,0))
        tick(avatar,1.0/60)
        assert(avatar.walking and avatar.animation.current_animation == "Walk")
    avatar.set_travel_velocity(Vector3.ZERO)
    tick(avatar,1.0/60)
    assert(not avatar.walking and avatar.animation.current_animation == "Idle")
    for speed in [.14,.12,.09,.16]:
        avatar.set_travel_velocity(Vector3(speed,0,0))
        tick(avatar,1.0/60)
        assert(not avatar.walking and avatar.animation.current_animation == "Idle")
    avatar.free()

    # Equal elapsed input should reach the same cadence at phone/desktop frame
    # rates. The initial acceleration must not jump straight to a fast gait.
    var rates: Array[float] = []
    for fps in [30,60,120]:
        avatar = actor()
        avatar.set_travel_velocity(Vector3(4.8,0,0))
        tick(avatar,1.0/fps)
        assert(avatar.animation.speed_scale > 1 and avatar.animation.speed_scale < 1.5)
        for frame in range(1,fps/3):
            tick(avatar,1.0/fps)
        rates.append(avatar.animation.speed_scale)
        assert(avatar.animation.current_animation == "Walk")
        # A cast keeps its authored timing while the next movement state changes.
        avatar.play_cast()
        avatar.set_travel_velocity(Vector3.ZERO)
        for frame in range(fps/2):
            tick(avatar,1.0/fps)
        assert(avatar.animation.current_animation == "Cast" and avatar.animation.speed_scale == 1)
        for frame in range(fps):
            tick(avatar,1.0/fps)
        assert(avatar.animation.current_animation == "Idle")
        avatar.free()
    assert(absf(rates[0]-rates[1]) < .001 and absf(rates[1]-rates[2]) < .001,
        "Cadence smoothing must not depend on render FPS")

    # Exercise the real remote interpolation caller, which previously used total
    # 3D displacement and a frame-dependent .003m walking cutoff.
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    await create_timer(.1).timeout
    app.start_preview()
    await create_timer(.1).timeout
    app.session.set_process(false)
    for fps in [30,60,120]:
        avatar = actor()
        app.session.remotes["motion-fixture"] = {"avatar":avatar,"target":Vector3(0,.3,0)}
        app.session._process(1.0/fps)
        assert(not avatar.walking and avatar.travel_speed == 0,
            "Remote caller must ignore vertical interpolation")
        avatar.position = Vector3.ZERO
        app.session.remotes["motion-fixture"].target = Vector3(.02,0,0)
        app.session._process(1.0/fps)
        assert(avatar.walking and is_equal_approx(avatar.travel_speed,.2),
            "A real slow remote mover must animate at every supported frame rate")
        app.session.remotes.erase("motion-fixture")
        avatar.free()
    app.queue_free()
    await process_frame
    print("AVATAR_MOTION_PASS: horizontal travel, jitter thresholds, 30/60/120 FPS cadence, cast return, remote caller")
    quit()
