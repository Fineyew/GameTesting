class_name VisualBenchmark
extends RefCounted
## Real engine assets/cameras; no grants or gameplay simulation. online.gd verifies casts.
static func capture(tree: SceneTree, name: String) -> void:
    await tree.create_timer(.15).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        tree.root.get_texture().get_image().save_png("user://"+name+".png")

static func check(app: Node, tree: SceneTree) -> void:
    for child in app.world.get_children():
        if child is DawnreefArt:
            var well = child.get_node("LanternWell") as MeshInstance3D
            # Transform vertices, not an already axis-aligned bounding box: rotating
            # the latter overestimates extents for a legitimately transformed import.
            var lowest := INF
            var highest := -INF
            for surface in well.mesh.get_surface_count():
                for vertex in well.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]:
                    var height: float = (well.transform * vertex).y
                    lowest = minf(lowest,height)
                    highest = maxf(highest,height)
            assert(lowest >= -.01 and highest > 3.3 and highest < 3.6,
                "Imported well must keep its walkable floor and upright floating vanes")
    var actor = app.session.player.avatar as WayfarerAvatar
    var skeleton = actor.find_child("Skeleton3D",true,false) as Skeleton3D
    assert(skeleton != null and skeleton.get_bone_count() == 13)
    var leg = skeleton.find_bone("ThighL")
    actor.animation.play("Walk")
    actor.animation.seek(.12,true)
    var before = skeleton.get_bone_pose_rotation(leg)
    actor.animation.seek(.48,true)
    assert(not before.is_equal_approx(skeleton.get_bone_pose_rotation(leg)),"Walk must animate the imported rig")
    actor.animation.play("Idle")
    var frame = Camera3D.new()
    app.world.add_child(frame)
    frame.fov = 60
    frame.position = Vector3(5.8,5.0,3.2)
    frame.look_at(Vector3(-3.8,1.3,-5.3))
    frame.make_current()
    await capture(tree,"benchmark")
    app.session.hud.hide()
    frame.position = Vector3(-1.7,1.8,-1.4)
    frame.look_at(Vector3(-4,1.17,-4))
    await capture(tree,"mara")
    var player = app.session.player.position
    frame.position = player+Vector3(1.8,1.85,-3.3)
    frame.look_at(player+Vector3.UP*1.1)
    await capture(tree,"wayfarer")
    var effect = GlimmerPresentation.new()
    app.world.add_child(effect)
    var origin = Vector3(10,1.45,-6)
    var target = Vector3(12,1,-10)
    frame.position = Vector3(16,3,-5)
    frame.look_at(origin.lerp(target,.5))
    var impacts = {"count":0}
    effect.impact.connect(func(): impacts.count += 1)
    effect.begin(origin,target)
    await tree.create_timer(1.25).timeout
    assert(impacts.count == 1 and not is_instance_valid(effect),"Spell must impact once and release its nodes")
    app.session.camera.camera.make_current()
    frame.queue_free()
    app.session.hud.show()
    # Exercise the real presentation method with a clearly isolated preview fixture.
    # online.gd separately proves it is reached only after an authoritative receipt.
    var before_position = app.session.player.position
    app.session.player.position = Vector3(10,0,-8)
    app.session.busy = true
    app.session.present_glimmer()
    await tree.create_timer(.3).timeout
    assert(not app.session.player.enabled and not app.session.hud.visible)
    await capture(tree,"glimmer")
    await tree.create_timer(.85).timeout
    assert(app.session.hud.visible and app.session.camera.camera.current)
    app.session.busy = false
    app.session.player.position = before_position
    app.session.hud.stick.axis = Vector2.RIGHT
    app.session.player.velocity.x = 4.8
    app.session.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
    assert(app.session.hud.stick.axis == Vector2.ZERO and app.session.player.velocity.x == 0)
    var paused_position = app.session.player.position
    await tree.create_timer(.25).timeout
    assert(not app.session.player.enabled)
    assert(Vector2(paused_position.x,paused_position.z).distance_to(Vector2(app.session.player.position.x,app.session.player.position.z)) < .001)
    app.session.notification(Node.NOTIFICATION_APPLICATION_RESUMED)
    await tree.process_frame
    assert(app.session.application_active)
    print("GODOT_ART_PASS")
