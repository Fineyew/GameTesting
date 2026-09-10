extends SceneTree

func _init() -> void:
    call_deferred("run")

func click_control(button: Button) -> void:
    # Dispatch through the GUI, not only pressed.emit(): input can still hold the
    # old panel when its callback replaces it. Native Android caught this path.
    var at = button.get_global_rect().get_center()
    for down in [true,false]:
        var event = InputEventMouseButton.new()
        event.position = at
        event.global_position = at
        event.button_index = MOUSE_BUTTON_LEFT
        event.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
        event.pressed = down
        root.push_input(event,true)
        await process_frame

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
    await app.session.show_inventory()
    assert(app.session.hud.modal)
    await create_timer(.2).timeout
    print("BROWSE_TOUCH_CENTER=",app.session.commerce_panel.browse_button.get_global_rect().get_center())
    await click_control(app.session.commerce_panel.browse_button)
    assert(app.session.commerce_panel.buy_buttons.buy_lanternkeeper_vest.disabled)
    assert(app.session.commerce_panel.equip_buttons.is_empty())
    app.session.hud.close_panel()
    await app.session.show_folio()
    assert(app.session.hud.modal and app.session.folio_panel.choices.is_empty())
    app.session.hud.close_panel()
    # Presentation fixture only; online.gd separately earns/saves through the API.
    var panel = app.session.hud.open_panel("Wayfarer's Folio")
    var folio = FolioPanel.new()
    panel.add_child(folio)
    folio.build({"known_spells":["glimmer_spark","root_snare","tide_mend"],"folio":["glimmer_spark","tide_mend"],"folio_capacity":6},false)
    assert(folio.choices.size() == 3 and not folio.choices.has("seam_lance"))
    folio.toggle_spell("seam_lance")
    assert(folio.selected.size() == 2)
    folio.choices.root_snare.pressed.emit()
    assert(folio.selected.size() == 3 and not folio.save_button.disabled)
    await create_timer(.2).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png("user://folio.png")
    app.session.hud.close_panel()
    # Server-shaped presentation fixture; real currency comes from online.gd's quests.
    var supply = CommercePanel.preview_view({"wallet":{"shell_chits":14},"level":2},"dawnreef_supply_cart")
    supply.shop.listings[0].can_buy = true
    var vendor = CommercePanel.new()
    app.session.hud.open_panel("Dawnreef Supply Cart").add_child(vendor)
    vendor.build(supply,false)
    assert(not vendor.buy_buttons.buy_lanternkeeper_vest.disabled)
    assert(vendor.buy_buttons.buy_sunthread_bandage.disabled)
    await create_timer(.2).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png("user://vendor.png")
    var vest = supply.shop.listings[0].duplicate()
    vest.owned = 1
    vest.equipped = true
    vest.current_guard = 1
    vest.guard_delta = 0
    var equipment = CommercePanel.new()
    app.session.hud.open_panel("Bag & equipment").add_child(equipment)
    equipment.build({"character":{"wallet":{"shell_chits":2},"level":2,"equipment":{"chest":"lanternkeeper_vest"}},"stats":{"guard":1},"items":[vest]},false,"Equipment saved.")
    assert(equipment.unequip_button != null and equipment.equip_buttons.is_empty())
    await create_timer(.2).timeout
    if DisplayServer.get_name() != "headless":
        await RenderingServer.frame_post_draw
        root.get_texture().get_image().save_png("user://equipment.png")
    app.session.hud.close_panel()
    app.session.show_settings()
    assert(app.session.hud.modal)
    app.return_to_gateway()
    assert(app.gateway.visible)
    app.queue_free()
    await process_frame
    print("GODOT_SMOKE_PASS")
    quit()
