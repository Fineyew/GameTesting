extends SceneTree

func _init() -> void:
    call_deferred("run")

func run() -> void:
    var fixture = JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
    var world = Node3D.new()
    root.add_child(world)
    var samples := 0
    var rays := 0
    for case in fixture.cases:
        var terrain = TerrainSurface.new()
        assert(terrain.configure(case.surface).is_empty(), case.name)
        for probe in case.probes:
            assert(absf(terrain.sample(probe[0],probe[1]).height-probe[2]) < 0.000001, case.name)
        for query in case.expected_samples:
            var actual = terrain.sample(query.at[0],query.at[1])
            var expected = query.result
            assert(absf(actual.height-expected.height) < 0.000001, case.name+" height")
            assert(absf(actual.slope_degrees-expected.slope_degrees) < 0.000001, case.name+" slope")
            assert(actual.cell[0] == int(expected.cell[0]) and actual.cell[1] == int(expected.cell[1]) and actual.triangle == int(expected.triangle), case.name+" ownership")
            samples += 1
        var triangles = terrain.triangles()
        assert(triangles.size() == case.expected_triangles.size(), case.name+" triangle count")
        for i in range(triangles.size()):
            for j in range(3):
                for k in range(3):
                    assert(absf(triangles[i][j][k]-case.expected_triangles[i][j][k]) < 0.000001, case.name+" triangles")
        var body = StaticBody3D.new()
        var collision = CollisionShape3D.new()
        collision.shape = terrain.collision_shape()
        body.add_child(collision)
        world.add_child(body)
        await physics_frame
        await physics_frame
        var space = world.get_world_3d().direct_space_state
        for i in range(case.rays.size()):
            var at = case.rays[i]
            var ray = PhysicsRayQueryParameters3D.create(Vector3(at[0],10,at[1]),Vector3(at[0],-10,at[1]))
            var hit = space.intersect_ray(ray)
            assert(not hit.is_empty(), case.name+" missing top collision")
            assert(absf(hit.position.y-case.expected_ray_heights[i]) < .0001, case.name+" physics height")
            rays += 1
        for ray in case.get("wall_rays",[]):
            var a = ray[0]
            var b = ray[1]
            var hit = space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(a[0],a[1],a[2]),Vector3(b[0],b[1],b[2])))
            assert(not hit.is_empty(),case.name+" missing riser")
            var coordinate: float = hit.position[int(case.get("wall_axis",0))]
            assert(absf(coordinate-1.0)<.0001 or absf(coordinate-2.0)<.0001,case.name+" wrong riser")
            rays += 1
        body.queue_free()
        await physics_frame
        await physics_frame
    for invalid in fixture.invalid:
        var terrain = TerrainSurface.new()
        assert(terrain.configure({"bounds":[0,0,1,1],"cells":{}}).is_empty())
        assert(not terrain.configure(invalid).is_empty(), "accepted invalid terrain")
        assert(terrain.sample(.5,.5).is_empty(), "retained stale terrain")
    var safe = TerrainSurface.new()
    assert(safe.configure({"bounds":[0,0,1,1],"cells":{}}).is_empty())
    assert(safe.sample(NAN,0).is_empty() and safe.sample(0,INF).is_empty())
    assert(safe.sample(-.00001,0).is_empty() and safe.sample(1.00001,0).is_empty())
    world.queue_free()
    await process_frame
    print("TERRAIN_PARITY_PASS cases=",fixture.cases.size()," samples=",samples," physics_rays=",rays," invalid=",fixture.invalid.size())
    quit()
