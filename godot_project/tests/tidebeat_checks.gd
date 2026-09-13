class_name TidebeatChecks
extends RefCounted
## Presentation fixtures never grant a live character spells, rewards or combat state.
static func fixture(action := "glimmer_spark") -> Dictionary:
    return JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/tidebeat.json")).frames[action].before

static func outcome(action: String) -> Dictionary:
    return JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/tidebeat.json")).frames[action].after

static func check(app: Node, tree: SceneTree, render := false) -> void:
    var session = app.session
    var at = session.player.position
    session.player.position = Vector3(10,0,-8)
    session.busy = true
    var original = session.character.duplicate(true)
    for key in ["shellfold_sifter","hushfin_ray"]:
        var creature = app.world.enemies[key] as ReefCreature
        assert(creature != null)
        var triangles := 0
        var meshes = creature.find_children("*","MeshInstance3D",true,false)
        assert(meshes.size() <= 16)
        for mesh_node in meshes:
            assert(mesh_node.material_override.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED)
            for surface in mesh_node.mesh.get_surface_count():
                var arrays = mesh_node.mesh.surface_get_arrays(surface)
                triangles += (arrays[Mesh.ARRAY_INDEX].size() if arrays[Mesh.ARRAY_INDEX] != null else arrays[Mesh.ARRAY_VERTEX].size())/3
        assert(triangles <= 600,"Each new creature must remain a small mobile silhouette")
        creature.set_process(false)
        creature.set_intent({"guard":6,"focus_drain":2})
        creature._process(1)
        assert(creature.guarded and creature.drawing_focus)
        var nodes = creature.plates if key == "shellfold_sifter" else creature.fins
        var pose = nodes[0].transform
        creature.set_intent({})
        creature._process(1)
        assert(nodes[0].transform != pose,"Authored intent motion must change the silhouette")
        creature.set_process(true)
        print("REEF_CREATURE=",key,":",triangles," triangles; ",meshes.size()," meshes")
    var before = fixture()
    var after = before.duplicate(true)
    after.enemy_vigor = 24
    after.player_vigor = 22
    after.focus = 5
    var signatures: Array[String] = []
    for key in TidebeatEffect.PROFILES:
        var effect = TidebeatEffect.new()
        app.world.add_child(effect)
        effect.configure(key,Vector3(10,1.1,-8),Vector3(12,1,-10))
        effect.set_process(false)
        assert(effect.pieces.size() <= TidebeatEffect.MAX_MESHES)
        var triangles := 0
        var signature := ""
        for piece in effect.pieces:
            assert(piece.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF)
            assert(piece.material_override.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED)
            assert(piece.material_override.next_pass == null)
            for surface in piece.mesh.get_surface_count():
                triangles += piece.mesh.surface_get_arrays(surface)[Mesh.ARRAY_INDEX].size()/3
            signature += str(piece.mesh.get_class(),piece.mesh.get_aabb(),piece.transform)
        assert(triangles <= 4000,"Bound total spell geometry, including all rings")
        assert(not signatures.has(signature),"Spell silhouettes must differ without color")
        signatures.append(signature)
        var events = {"impact":0,"finish":0}
        effect.impact.connect(func(): events.impact += 1)
        effect.finished.connect(func(): events.finish += 1)
        effect._process(effect.duration*.55)
        effect._process(effect.duration)
        effect._process(effect.duration)
        assert(events.impact == 1 and events.finish == 1)
        await tree.process_frame
    var saved_scale = tree.root.scaling_3d_scale
    var saved_shadows = app.world.sun.shadow_enabled
    for quality in (["low","high"] if render else ["low"]):
        tree.root.scaling_3d_scale = .75 if quality == "low" else 1.0
        app.world.sun.shadow_enabled = quality == "high"
        for key in TidebeatEffect.PROFILES:
            session.short_spell_effects = false
            session.reduced_motion = false
            var authored = fixture(key)
            assert(authored.spells.size() <= 6)
            app.world.show_intent(authored)
            session.player.position = app.world.enemy.position+Vector3(-2,0,2)
            session.camera.follow(session.player)
            session.playback.play(key,authored,outcome(key),"fixture-"+quality+key)
            assert(session.playback.active and not session.hud.visible)
            # Freeze one authored impact silhouette; runtime completion is checked below.
            session.playback.effect.set_process(false)
            session.playback.effect.update_pose(.58)
            if render:
                await VisualBenchmark.capture(tree,"spell-"+quality+"-"+key)
                print("SPELL_RENDER=",quality,":",key,":",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),":",RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME))
            session.playback.stop()
            await tree.process_frame
            assert(session.hud.visible and session.camera.camera.is_current())
            assert(session.character == original,"Presentation mutated the real character")
    tree.root.scaling_3d_scale = saved_scale
    app.world.sun.shadow_enabled = saved_shadows
    # Actual GUI skip dispatch must survive freeing the emitting panel.
    session.playback.play("root_snare",before,after,"skip-fixture")
    await tree.process_frame
    await tree.process_frame
    var button = session.playback.skip_button
    assert(button.size.y >= 56)
    var center = button.get_global_rect().get_center()
    for down in [true,false]:
        var event = InputEventMouseButton.new()
        event.position = center
        event.global_position = center
        event.button_index = MOUSE_BUTTON_LEFT
        event.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
        event.pressed = down
        tree.root.push_input(event,true)
        await tree.process_frame
    assert(not session.playback.active and session.hud.visible)
    var count = session.playback.serial
    await session.playback.play("root_snare",before,after,"skip-fixture")
    assert(session.playback.serial == count,"A repeated receipt must not replay")
    # Reduced motion preserves static silhouettes and the actual gameplay camera.
    session.reduced_motion = true
    session.playback.play("seam_lance",before,after,"reduced-fixture")
    assert(session.camera.camera.is_current() and session.playback.frame == null)
    var effect = session.playback.effect
    effect.set_process(false)
    var transforms: Array[Transform3D] = []
    for piece in effect.pieces:
        transforms.append(piece.global_transform)
    for progress in [.15,.5,.9]:
        effect.update_pose(progress)
        for i in effect.pieces.size():
            assert(effect.pieces[i].global_transform == transforms[i])
    if render:
        await VisualBenchmark.capture(tree,"spell-reduced")
    session.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
    assert(not session.playback.active and session.hud.visible and session.camera.camera.is_current())
    count = session.playback.serial
    await session.playback.play("brace",before,after,"background-fixture")
    session.notification(Node.NOTIFICATION_APPLICATION_RESUMED)
    await session.playback.play("brace",before,after,"background-fixture")
    assert(session.playback.serial == count,"Resume must not replay a background receipt")
    session.reduced_motion = false
    session.short_spell_effects = true
    session.playback.play("gather",before,after,"short-fixture")
    assert(session.playback.effect.duration < .5 and session.camera.camera.is_current())
    assert(is_equal_approx(session.player.avatar.animation.speed_scale,2.6))
    await session.playback.finished
    assert(session.hud.visible and not session.playback.active)
    session.short_spell_effects = false
    # A clearly isolated server-shaped UI fixture; restore it before returning.
    assert(session.preview)
    session.character = original.duplicate(true)
    session.character.encounter = before
    session.show_combat()
    await tree.process_frame
    await tree.process_frame
    var actions = session.hud.panel_content.find_children("*","Button",true,false)
    assert(actions.size() >= 8)
    for choice_button in actions:
        assert(choice_button.size.y >= 56)
    var intent = app.world.enemy.get_node("TidebeatIntent")
    assert(intent.visible and "Mark +6" in intent.text and "damage before protection" in intent.text)
    if render:
        await VisualBenchmark.capture(tree,"combat-controls")
    session.character = original
    app.world.show_intent({})
    tree.root.get_node("Soundscape").set_combat(false)
    session.hud.close_panel()
    session.player.position = at
    session.busy = false
    assert(session.character == original)
    print("TIDEBEAT_PRESENTATION_PASS: eleven distinct bounded silhouettes, GUI skip, receipt deduplication, static reduced mode, camera restoration, pause/resume and no character writes")
