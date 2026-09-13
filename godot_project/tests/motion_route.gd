extends SceneTree
## Deterministic in-place rig study, not real-time or device FPS evidence.
var app: Node
var actor: WayfarerAvatar
var frame := 0
var caption: Label

func _init() -> void:
    call_deferred("begin")

func begin() -> void:
    app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    app.start_preview()
    app.session.set_process(false)
    app.session.player.set_physics_process(false)
    app.session.player.position = Vector3(0,0,5)
    app.session.hud.hide()
    actor = app.session.player.avatar
    actor.rotation.y = -.55
    var camera = Camera3D.new()
    app.world.add_child(camera)
    camera.position = Vector3(2.3,1.5,1.8)
    camera.look_at(Vector3(0,.95,5))
    camera.make_current()
    var overlay = CanvasLayer.new()
    app.add_child(overlay)
    caption = Label.new()
    caption.position = Vector2(32,32)
    caption.add_theme_font_size_override("font_size",26)
    caption.add_theme_color_override("font_color",Color("fff0cf"))
    caption.add_theme_color_override("font_shadow_color",Color("173336"))
    caption.add_theme_constant_override("shadow_offset_x",2)
    caption.add_theme_constant_override("shadow_offset_y",2)
    overlay.add_child(caption)

func _process(_delta: float) -> bool:
    if actor == null:
        return false
    frame += 1
    if frame <= 75:
        actor.set_travel_velocity(Vector3(1.8,0,0))
        caption.text = "Veilbound Tides · Walk"
    elif frame <= 150:
        actor.set_travel_velocity(Vector3(4.8,0,0))
        caption.text = "Veilbound Tides · Run"
    elif frame <= 210:
        actor.set_travel_velocity(Vector3(.5,0,0))
        actor.turn_error = 1.0 if frame <= 180 else -1.0
        caption.text = "Veilbound Tides · Turning steps"
    else:
        actor.set_travel_velocity(Vector3.ZERO)
        if frame == 211:
            actor.play_cast()
            caption.text = "Veilbound Tides · Cast"
        elif frame == 249:
            actor.play_hit()
            caption.text = "Veilbound Tides · Hit and recovery"
        elif frame == 310:
            app.queue_free()
            print("MOTION_ROUTE_PASS")
            quit()
    return false
