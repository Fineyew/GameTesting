extends SceneTree

func _init() -> void:
    call_deferred("run")

func run() -> void:
    var fixture = JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
    var failures: Array = []
    for scenario in fixture.cases:
        var player = WayfarerController.new()
        root.add_child(player)
        player.set_physics_process(false)
        player.geometry = fixture.geometry
        player.terrain = TerrainSurface.new()
        assert(player.terrain.configure(fixture.geometry.terrain).is_empty())
        player.networked = true
        player.reconcile(Vector3(scenario.start[0],player.terrain.sample(scenario.start[0],scenario.start[1]).height,scenario.start[1]))
        var max_error = 0.0
        var final_error = 0.0
        var max_correction = 0.0
        var last_unsettled = 0
        for tick in scenario.frames.size():
            var frame = scenario.frames[tick]
            player.enabled = frame.connected
            player.input_axis = Vector2(frame.axis[0],frame.axis[1])
            if frame.reset:
                player.has_snapshot = false
            if frame.snapshot != null:
                player.reconcile(Vector3(frame.snapshot[0],frame.snapshot[1],frame.snapshot[2]))
            # Compare with the same controller tick without network correction.
            var before = player.position
            var velocity_before = player.velocity
            player.networked = false
            player._physics_process(1.0/60)
            var predicted = player.position
            player.position = before
            player.velocity = velocity_before
            player.networked = true
            player._physics_process(1.0/60)
            max_correction = maxf(max_correction,Vector2(predicted.x-player.position.x,predicted.z-player.position.z).length())
            var server = Vector3(frame.server[0],frame.server[1],frame.server[2])
            final_error = player.position.distance_to(server)
            max_error = maxf(max_error,final_error)
            if tick>=120 and final_error>.03: last_unsettled=tick
            assert(absf(player.position.y-player.terrain.sample(player.position.x,player.position.z).height)<.0001,"feet left surface")
            assert(TerrainTraversal.clear(player.terrain,Vector2(player.position.x,player.position.z),Vector2(player.position.x,player.position.z),fixture.geometry.blockers),"prediction entered forbidden terrain")
        print("NETWORK_CASE ",scenario.name," peak=",snappedf(max_error,.001)," correction=",snappedf(max_correction,.001)," final=",snappedf(final_error,.001)," settled_after_release_s=",maxf(0,(last_unsettled+1-120)/60.0))
        if final_error>.03 or last_unsettled>270 or max_correction>.101 or max_error>2.5:
            failures.append(scenario.name)
        player.free()
    if not failures.is_empty():
        push_error("Unsettled network scenarios: "+str(failures))
        quit(1)
        return
    print("MOVEMENT_NETWORK_PASS cases=",fixture.cases.size())
    quit()
