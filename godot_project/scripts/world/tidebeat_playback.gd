class_name TidebeatPlayback
extends Node
## Displays one confirmed receipt. Skips, speed and lifecycle have no gameplay writes.
signal finished
var session: Node
var active := false
var effect: TidebeatEffect
var frame: Camera3D
var overlay: Control
var caption: Label
var skip_button: Button
var shown: Array[String] = []
var presented: Dictionary = {}
var enemy_scale := Vector3.ONE
var reaction: Tween
var serial := 0
var speed := 1.0

func play(action: String, before: Dictionary, after: Dictionary, receipt: String) -> void:
    if shown.has(receipt) or not TidebeatEffect.PROFILES.has(action):
        return
    shown.append(receipt)
    if shown.size() > 32:
        shown.pop_front()
    if not session.application_active:
        return
    if active:
        stop()
    serial += 1
    active = true
    speed = 2.6 if session.short_spell_effects else 1.0
    presented[action] = int(presented.get(action,0))+1
    session.hud.close_panel()
    session.hud.hide()
    session.world.show_intent(before)
    var intent_label = session.world.enemy.get_node_or_null("TidebeatIntent")
    if intent_label:
        intent_label.hide() # The receipt overlay owns the action readout during playback.
    enemy_scale = session.world.enemy.scale
    var from = session.player.global_position+Vector3.UP*1.1
    var to = session.world.enemy.global_position+Vector3.UP
    if from.distance_to(to) > .1 and not session.reduced_motion:
        session.player.avatar.look_at(Vector3(to.x,session.player.avatar.global_position.y,to.z))
    if action in ["tide_mend","gather"]:
        session.player.avatar.play_recovery(speed)
    else:
        session.player.avatar.play_cast(speed)
    if not session.short_spell_effects and not session.reduced_motion:
        var at = OrbitRig.pair_frame(session.world.get_world_3d(),from,to,session.player.get_rid())
        if at.is_finite():
            frame = Camera3D.new()
            session.world.add_child(frame)
            frame.position = at
            frame.look_at(from.lerp(to,.5))
            frame.fov = 60
            frame.make_current()
    build_overlay(action,before,after)
    effect = TidebeatEffect.new()
    session.world.add_child(effect)
    effect.configure(action,from,to,session.reduced_motion,speed)
    effect.impact.connect(on_impact.bind(action,before,after))
    effect.finished.connect(stop)
    get_node("/root/Soundscape").cue(TidebeatEffect.PROFILES[action][3])
    await finished

func build_overlay(action: String, before: Dictionary, after: Dictionary) -> void:
    overlay = Control.new()
    overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
    overlay.theme = TideUI.theme()
    add_child(overlay)
    var plaque = PanelContainer.new()
    plaque.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
    plaque.offset_left = 24
    plaque.offset_right = -24
    plaque.offset_top = 20
    overlay.add_child(plaque)
    var rows = VBoxContainer.new()
    plaque.add_child(rows)
    var detail = CombatReadout.describe(action,before.get("spells",{}))
    rows.add_child(TideUI.label("%s · %s" % [detail.name,detail.family],24,TideUI.GOLD))
    var target = before.get("enemy_name","Foe") if detail.target == "Foe" else "You"
    var mark_used = int(before.get("mark",0))-int(after.get("mark",0))
    if mark_used > 0:
        detail.effect += " · Mark +%s" % mark_used
    rows.add_child(TideUI.paragraph("%s · %s Focus · %s" % [target,detail.cost,detail.effect],19))
    var heading = "Presentation preview" if session.preview else "Result saved"
    rows.add_child(TideUI.paragraph(heading+" · Your Vigor %s → %s · Foe Vigor %s → %s · Focus %s → %s" % [int(before.get("player_vigor",30)),int(after.get("player_vigor",30)),int(before.get("enemy_vigor",0)),int(after.get("enemy_vigor",0)),int(before.get("focus",3)),int(after.get("focus",3))],17))
    caption = TideUI.label("",19,TideUI.PAPER)
    rows.add_child(caption)
    get_node("/root/Soundscape").caption_requested.connect(show_caption)
    skip_button = TideUI.button("Skip animation",stop)
    skip_button.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
    skip_button.offset_left = -236
    skip_button.offset_right = -24
    skip_button.offset_top = -84
    skip_button.offset_bottom = -24
    overlay.add_child(skip_button)

func show_caption(words: String) -> void:
    if is_instance_valid(caption):
        caption.text = words

func on_impact(action: String, before: Dictionary, after: Dictionary) -> void:
    if not active:
        return
    get_node("/root/Soundscape").cue(TidebeatEffect.PROFILES[action][4])
    if int(after.get("enemy_vigor",0)) < int(before.get("enemy_vigor",0)) and not session.reduced_motion:
        reaction = create_tween()
        reaction.tween_property(session.world.enemy,"scale",enemy_scale*Vector3(1.1,.85,1.1),.1)
        reaction.tween_property(session.world.enemy,"scale",enemy_scale,.22)
    var before_vigor = int(before.get("player_vigor",30))
    var after_vigor = int(after.get("player_vigor",30))
    if after_vigor < before_vigor:
        session.player.avatar.play_hit(speed)
        get_node("/root/Soundscape").cue(session.world.creature_cue())
    elif after_vigor > before_vigor:
        session.player.avatar.play_recovery(speed)
    if after_vigor >= before_vigor and int(after.get("last_focus_loss",0)) > 0:
        get_node("/root/Soundscape").cue(session.world.creature_cue())

func stop() -> void:
    if not active:
        return
    active = false
    if reaction:
        reaction.kill()
        reaction = null
    if is_instance_valid(session.world.enemy):
        session.world.enemy.scale = enemy_scale
    if is_instance_valid(effect):
        effect.finished.disconnect(stop)
        effect.finish()
    effect = null
    if is_instance_valid(session.player):
        session.player.avatar.finish_action_pose()
    if is_instance_valid(session.camera):
        session.camera.camera.make_current()
    if is_instance_valid(frame):
        frame.queue_free()
    frame = null
    if is_instance_valid(overlay):
        overlay.hide()
        overlay.queue_free() # Keep the skip button alive until native input dispatch ends.
    overlay = null
    caption = null
    var sound = get_node_or_null("/root/Soundscape")
    if sound and sound.caption_requested.is_connected(show_caption):
        sound.caption_requested.disconnect(show_caption)
    if is_instance_valid(session.hud):
        session.hud.show()
    var intent_label = session.world.enemy.get_node_or_null("TidebeatIntent")
    if intent_label and session.character.get("encounter",{}).get("state") == "active":
        intent_label.show()
    finished.emit()

func _exit_tree() -> void:
    stop()
