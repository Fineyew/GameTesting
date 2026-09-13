class_name MotionVisuals
extends RefCounted
## Render the real shared rig, including every existing appearance in a full room.
static func check(app: Node, tree: SceneTree) -> void:
    if DisplayServer.get_name() == "headless":
        return
    var session = app.session
    session.set_process(false)
    session.player.set_physics_process(false)
    session.player.hide()
    session.hud.hide()
    var actors: Array[WayfarerAvatar] = []
    var frame = Camera3D.new()
    app.world.add_child(frame)
    frame.fov = 60
    frame.position = Vector3(0,7.5,22)
    frame.look_at(Vector3(0,1,8))
    frame.make_current()
    for index in 32:
        var actor = WayfarerAvatar.new()
        app.world.add_child(actor)
        actor.build({"robe":["teal","coral","indigo"][index%3],"skin":["warm","deep","pale"][floori(index/3.0)%3]})
        actor.follow_terrain(app.world.terrain)
        actor.position = Vector3((index%8-3.5)*1.65,0,5+floori(index/8.0)*1.8)
        actor.position.y = app.world.terrain.sample(actor.position.x,actor.position.z).height
        actor.rotation.y = PI-.25
        actor.set_travel_velocity(Vector3(4.8 if index%2 else 1.8,0,0))
        actors.append(actor)
    await tree.create_timer(.4).timeout
    await RenderingServer.frame_post_draw
    var visible_count := 0
    for actor in actors:
        if frame.is_position_in_frustum(actor.global_position+Vector3.UP):
            visible_count += 1
    assert(visible_count == 32,"Crowd sample must include all 32 actors")
    print("CROWD_RIGS=",visible_count)
    print("CROWD_DRAW_CALLS=",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
    print("CROWD_PRIMITIVES=",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
    print("CROWD_TEXTURE_BYTES=",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TEXTURE_MEM_USED))
    tree.root.get_texture().get_image().save_png("user://motion-crowd.png")
    for index in range(1,actors.size()):
        actors[index].queue_free()
    var actor = actors[0]
    actor.position = Vector3(0,0,5)
    actor.rotation.y = -.55
    actor.set_process(false)
    frame.position = actor.position+Vector3(2.3,1.5,-3.2)
    frame.look_at(actor.position+Vector3.UP*.95)
    for clip in ["Walk","Run","TurnLeft","TurnRight","Hit","Recovery"]:
        actor.animation.play(clip,0)
        actor.animation.seek(actor.animation.current_animation_length*.28,true)
        actor.animation.pause()
        await tree.create_timer(.12).timeout
        await RenderingServer.frame_post_draw
        tree.root.get_texture().get_image().save_png("user://motion-"+clip.to_lower()+".png")
    actor.queue_free()
    frame.queue_free()
    session.camera.camera.make_current()
    session.player.show()
    session.hud.show()
    session.player.set_physics_process(true)
    session.set_process(true)
    await tree.process_frame
    print("MOTION_VISUALS_PASS")
