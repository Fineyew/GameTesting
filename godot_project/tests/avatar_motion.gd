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
    var contacts = {"count":0}
    avatar.footstep.connect(func(): contacts.count += 1)
    # Reproduce a short physics gesture entirely between rendered frames.
    avatar.set_travel_velocity(Vector3(0,0,-1.4))
    avatar.set_travel_velocity(Vector3.ZERO)
    assert(contacts.count == 1,"A real movement onset must survive a slow render frame")
    avatar.set_travel_velocity(Vector3(0,3,0))
    assert(contacts.count == 1,"Vertical correction and idle must stay silent")
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
        assert(avatar.animation.current_animation == "Run")
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

    avatar = actor()
    for speed in [3.0,2.7,2.5]:
        avatar.set_travel_velocity(Vector3(speed,0,0))
        tick(avatar,.05)
        assert(avatar.running and avatar.animation.current_animation == "Run")
    avatar.set_travel_velocity(Vector3(2.3,0,0))
    tick(avatar,.05)
    assert(not avatar.running and avatar.animation.current_animation == "Walk")
    for speed in [2.5,2.7]:
        avatar.set_travel_velocity(Vector3(speed,0,0))
        tick(avatar,.05)
        assert(not avatar.running)
    avatar.play_hit()
    tick(avatar,.21)
    assert(avatar.animation.current_animation == "Recovery")
    tick(avatar,.37)
    tick(avatar,.02)
    assert(avatar.animation.current_animation == "Walk")
    # Casts and their confirmed hit/recovery timing are independent of gait rate.
    avatar.play_cast()
    avatar.play_hit()
    assert(avatar.cast_remaining == 0 and avatar.animation.speed_scale == 1)
    avatar.free()

    var headings: Array[float] = []
    for fps in [30,60,120]:
        avatar = actor()
        avatar.set_travel_velocity(Vector3(.5,0,0))
        avatar.face_travel(PI/2,1.0/fps)
        tick(avatar,1.0/fps)
        assert(avatar.animation.current_animation == "TurnLeft")
        for frame in range(1,fps/3):
            avatar.face_travel(PI/2,1.0/fps)
        headings.append(avatar.rotation.y)
        avatar.free()
    assert(absf(headings[0]-headings[2]) < .001,"Turning must follow elapsed time")

    # Sample the actual imported skeleton after the editable library is applied.
    # Both soles stay level and the stance ankle moves back at reference speed.
    avatar = actor()
    var skeleton = avatar.model.find_child("Skeleton3D",true,false) as Skeleton3D
    for clip in ["Walk","Run"]:
        var duration = avatar.animation.get_animation(clip).length
        var duty = .33 if clip == "Run" else .52
        var speed = 4.0 if clip == "Run" else 1.8
        var previous := Vector3.INF
        for sample in 61:
            var time = float(sample)/60*duration
            avatar.animation.play(clip,0)
            avatar.animation.seek(time,true)
            avatar.animation.advance(0)
            skeleton.force_update_all_bone_transforms()
            for side in ["L","R"]:
                var index = skeleton.find_bone("Foot"+side)
                var foot = skeleton.get_bone_global_pose(index)
                assert(foot.origin.y >= .133,"Foot penetrates ground: %s %s sample%s %s" % [clip,side,sample,foot.origin])
                var up = foot.basis*skeleton.get_bone_global_rest(index).basis.inverse()*Vector3.UP
                assert(up.distance_to(Vector3.UP) < .001,"Soles stay level")
                if side == "L" and time/duration < duty-.02:
                    assert(absf(foot.origin.y-.135) < .002,"Stance foot stays grounded")
                    if previous.is_finite():
                        assert(absf((foot.origin.z-previous.z)/(duration/60)-speed) < .025,"Stance cannot skate at reference cadence")
                    previous = foot.origin
    avatar.free()

    # Near/far resources keep the same material semantics and named bind poses.
    for is_mara in [false,true]:
        avatar = WayfarerAvatar.new()
        root.add_child(avatar)
        avatar.build({"robe":"coral","skin":"deep"},is_mara)
        avatar.set_process(false)
        var near_names: Array = []
        for index in avatar.near_mesh.get_surface_count():
            near_names.append(avatar.near_mesh.surface_get_material(index).resource_name)
            assert(near_names[index] == avatar.far_mesh.surface_get_material(index).resource_name)
        assert(avatar.near_skin.get_bind_count() == avatar.far_skin.get_bind_count())
        for index in avatar.near_skin.get_bind_count():
            assert(avatar.near_skin.get_bind_name(index) == avatar.far_skin.get_bind_name(index))
            assert(avatar.near_skin.get_bind_pose(index).is_equal_approx(avatar.far_skin.get_bind_pose(index)))
        var rig_before = avatar.animation
        avatar.update_detail(9)
        assert(avatar.distant and avatar.body.mesh == avatar.far_mesh)
        avatar.update_detail(8)
        assert(avatar.distant,"LOD threshold must not flicker")
        avatar.update_detail(7)
        assert(not avatar.distant and avatar.body.mesh == avatar.near_mesh)
        assert(avatar.animation == rig_before and avatar.current_appearance == {"robe":"coral","skin":"deep"})
        avatar.free()

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
    # Exact terrain modifier output at a .3m stair edge, including the lowered
    # pelvis needed to reach the lower tread. This uses the real engine callback.
    var surface = TerrainSurface.new()
    assert(surface.configure({"bounds":[-1,-1,1,1],"cells":{"1:0":[300,300,300,300],"1:1":[300,300,300,300]}}).is_empty())
    avatar = actor()
    avatar.position = Vector3(0,.3,0)
    avatar.follow_terrain(surface)
    var rig = avatar.model.find_child("Skeleton3D",true,false) as Skeleton3D
    var modifier = rig.get_child(rig.get_child_count()-1) as WayfarerFooting
    var contact_checks = {"count":0}
    modifier.modification_processed.connect(func():
        for side in ["L","R"]:
            var foot = rig.to_global(rig.get_bone_global_pose(rig.find_bone("Foot"+side)).origin)
            assert(absf(foot.y-surface.sample(foot.x,foot.z).height-.135) < .003,"Both feet must reach their stair tread")
        contact_checks.count += 1)
    var at_before = avatar.position
    await create_timer(.12).timeout
    assert(contact_checks.count > 0 and avatar.position == at_before,"Foot fitting must not move the controller")
    avatar.free()
    app.queue_free()
    await process_frame
    print("AVATAR_MOTION_PASS: horizontal travel, Walk/Run hysteresis, 30/60/120 FPS cadence/turns, cast/hit/recovery, planted soles, remote caller")
    var audio = root.get_node_or_null("Soundscape")
    if audio:
        await audio.shutdown()
    quit.call_deferred()
