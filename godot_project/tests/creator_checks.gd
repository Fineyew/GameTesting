class_name CreatorChecks
extends RefCounted

static func colors(avatar: WayfarerAvatar) -> Dictionary:
    var found: Dictionary = {}
    for part in avatar.model.find_children("*","MeshInstance3D",true,false):
        for surface in part.mesh.get_surface_count():
            var source = part.mesh.surface_get_material(surface)
            if source.resource_name in ["RobeTint","SkinTint"]:
                var actual = part.get_active_material(surface).albedo_color.to_html(false)
                assert(not found.has(source.resource_name) or found[source.resource_name] == actual)
                found[source.resource_name] = actual
    assert(found.size() == 2,"Both appearance materials must be present on the real rig")
    return found

static func click(tree: SceneTree, control: Control) -> void:
    var at = control.get_global_rect().get_center()
    for down in [true,false]:
        var event = InputEventMouseButton.new()
        event.position = at
        event.global_position = at
        event.button_index = MOUSE_BUTTON_LEFT
        event.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
        event.pressed = down
        tree.root.push_input(event,true)
        await tree.process_frame

static func choose(option: OptionButton, index: int) -> void:
    option.select(index)
    option.item_selected.emit(index)

static func capture(tree: SceneTree, name: String) -> void:
    await tree.create_timer(.2).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        tree.root.get_texture().get_image().save_png("user://"+name+".png")

static func check(app: Node, tree: SceneTree) -> void:
    app.show_creator()
    await tree.process_frame
    await tree.process_frame
    var preview = app.identity_preview as WayfarerPreview
    var rig = preview.avatar.model
    assert(preview.viewport.find_world_3d() != app.world.get_world_3d(),"Preview must use an isolated world")
    assert(tree.root.get_camera_3d() == app.panorama,"Creator must not steal the world camera")
    var robes = ["287d7e","c66a61","665997"]
    var skins = ["c38d65","795443","e3baa0"]
    var compare = WayfarerAvatar.new()
    app.world.add_child(compare)
    compare.build({})
    compare.hide()
    for robe in 3:
        for skin in 3:
            choose(app.creator_robe,robe)
            choose(app.creator_skin,skin)
            var actual = colors(preview.avatar)
            assert(actual == {"RobeTint":robes[robe],"SkinTint":skins[skin]},"Creator choice was not visibly applied")
            compare.apply_appearance({"robe":app.ROBE_IDS[robe],"skin":app.SKIN_IDS[skin]})
            assert(colors(compare) == actual,"Creator and world colors differ")
            assert(preview.avatar.model == rig,"Changing color must not allocate another rig")
            if robe == skin:
                await capture(tree,["creator-teal","creator-coral","creator-indigo"][robe])
    assert(WayfarerAvatar.appearance_materials.size() == 6,"Tint cache must remain bounded by existing choices")
    preview.set_appearance({"robe":"old-unknown","skin":"old-unknown"})
    assert(colors(preview.avatar) == {"RobeTint":robes[0],"SkinTint":skins[0]},"Old appearance fallback changed")
    preview.set_appearance({})
    assert(colors(preview.avatar) == {"RobeTint":robes[0],"SkinTint":skins[0]})
    compare.queue_free()
    choose(app.creator_robe,2)
    choose(app.creator_skin,2)
    var before = preview.avatar.rotation.y
    await click(tree,preview.turn_left)
    assert(absf(angle_difference(before,preview.avatar.rotation.y)) > .7,"Rotation button input did not arrive")
    await click(tree,preview.reset_button)
    assert(is_zero_approx(angle_difference(preview.FRONT,preview.avatar.rotation.y)))
    # Dispatch actual touch through the root viewport, including a second finger.
    var at = preview.surface.get_global_rect().get_center()
    var touch = InputEventScreenTouch.new()
    touch.position = at
    touch.index = 3
    touch.pressed = true
    tree.root.push_input(touch,true)
    var other = InputEventScreenTouch.new()
    other.position = at
    other.index = 4
    other.pressed = true
    tree.root.push_input(other,true)
    var drag = InputEventScreenDrag.new()
    drag.position = at+Vector2(60,0)
    drag.relative = Vector2(60,0)
    drag.index = 3
    tree.root.push_input(drag,true)
    touch.pressed = false
    touch.position = drag.position
    tree.root.push_input(touch,true)
    other.pressed = false
    tree.root.push_input(other,true)
    assert(absf(angle_difference(preview.FRONT,preview.avatar.rotation.y)) > .5,"Touch rotation did not arrive")
    assert(preview.touch_index == -1)
    await capture(tree,"creator-rotated")
    preview.hide()
    assert(preview.viewport.render_target_update_mode == SubViewport.UPDATE_DISABLED)
    preview.show()
    assert(preview.viewport.render_target_update_mode == SubViewport.UPDATE_ALWAYS)
    await click(tree,preview.reset_button)
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        print("CREATOR_DRAW_CALLS=",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME))
    # Check both the narrow tablet layout and a wide phone layout, with safe insets.
    var original_size = tree.root.size
    var original_scale = tree.root.content_scale_size
    tree.root.content_scale_size = Vector2i.ZERO
    for dimensions in [Vector2i(960,720),Vector2i(1600,720)]:
        tree.root.size = dimensions
        for side in ["left","right"]:
            app.gateway_margin.add_theme_constant_override("margin_"+side,58)
        await tree.process_frame
        await tree.process_frame
        await tree.create_timer(.15).timeout
        assert(preview.get_global_rect().end.x <= app.card_scroll.get_global_rect().position.x)
        assert(preview.turn_left.size.y >= 56 and preview.turn_right.size.y >= 56)
        assert(preview.get_global_rect().position.x >= 58)
        assert(preview.get_global_rect().end.y <= dimensions.y-42,"Preview must remain inside the vertical safe margin")
        assert(app.card_scroll.get_global_rect().end.x <= dimensions.x-58)
        for point in [Vector3(-.95,0,0),Vector3(.95,2.25,0)]:
            assert(preview.camera.is_position_in_frustum(preview.avatar.global_transform*point),"Avatar must fit at narrow and wide aspects")
        await capture(tree,"creator-tablet" if dimensions.x == 960 else "creator-wide")
    tree.root.size = original_size
    tree.root.content_scale_size = original_scale
    for side in ["left","right"]:
        app.gateway_margin.add_theme_constant_override("margin_"+side,42)
    await tree.create_timer(.2).timeout
    app.show_character({"id":"preview-fixture","name":"Reef Tester","level":1,"appearance":{"robe":"coral","skin":"deep"}})
    await tree.process_frame
    await tree.process_frame
    await tree.create_timer(.2).timeout
    assert(not is_instance_valid(preview),"Creator viewport must release on selection")
    assert(colors(app.identity_preview.avatar) == {"RobeTint":robes[1],"SkinTint":skins[1]})
    assert(app.identity_preview.get_global_rect().end.y <= app.get_viewport_rect().size.y-42,"Selection preview must fit after a form swap")
    await capture(tree,"creator-selection")
    # Clearing/reopening must not accumulate invisible rendering worlds.
    for iteration in 3:
        var old = app.identity_preview
        app.show_creator()
        await tree.process_frame
        assert(not is_instance_valid(old))
        assert(app.identity_column.find_children("*","SubViewport",true,false).size() == 1)
    var last = app.identity_preview
    app.start_preview()
    await tree.process_frame
    assert(not is_instance_valid(last) and app.identity_preview == null)
    assert(tree.root.get_camera_3d() == app.session.camera.camera)
    app.return_to_gateway()
    await tree.process_frame
    assert(app.identity_column.find_children("*","SubViewport",true,false).is_empty())
    print("CREATOR_PREVIEW_PASS: nine choices, fallback, live rig reuse, GUI/touch rotation, aspect/safe-inset layout and cleanup")
