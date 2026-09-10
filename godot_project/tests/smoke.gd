extends SceneTree

func _init() -> void:
    call_deferred("run")

func run() -> void:
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    await create_timer(1).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png("user://gateway.png")
    app.start_preview()
    await create_timer(.4).timeout
    assert(app.session.player != null,"player did not spawn")
    var before = app.session.player.position.z
    app.session.hud.stick.axis = Vector2(0,-1)
    await create_timer(.8).timeout
    assert(app.session.player.position.z < before-1,"movement did not advance")
    app.session.hud.stick.release()
    await create_timer(.3).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png("user://dawnreef.png")
        print("DRAW_CALLS=",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
    app.session.show_inventory()
    assert(app.session.hud.modal)
    app.session.hud.close_panel()
    app.session.show_settings()
    assert(app.session.hud.modal)
    app.return_to_gateway()
    assert(app.gateway.visible)
    app.queue_free()
    await process_frame
    print("GODOT_SMOKE_PASS")
    quit()
