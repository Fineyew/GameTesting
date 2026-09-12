class_name TouchStick
extends Control
var axis := Vector2.ZERO
var finger := -1
var mouse_drag := false

func _ready() -> void:
    custom_minimum_size = Vector2(176,176)
    mouse_filter = Control.MOUSE_FILTER_STOP

func _draw() -> void:
    var center = size/2
    draw_circle(center, 78, Color(0.04,.13,.16,.55))
    draw_arc(center,78,0,TAU,48,Color(.84,.72,.48,.55),2,true)
    draw_circle(center + axis*52,28,Color(.85,.76,.57,.88))

func _gui_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch and event.pressed:
        finger = event.index
        update_axis(event.position)
    elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
        mouse_drag = event.pressed
        if mouse_drag:
            update_axis(event.position)
        else:
            release()
    elif event is InputEventMouseMotion and mouse_drag:
        update_axis(event.position)

func _input(event: InputEvent) -> void:
    if event is InputEventScreenDrag and event.index == finger:
        update_axis(event.position-global_position)
    if event is InputEventScreenTouch and event.index == finger and not event.pressed:
        release()
    if event is InputEventMouseButton and not event.pressed and mouse_drag:
        release()

func update_axis(at: Vector2) -> void:
    axis = ((at-size/2)/52).limit_length()
    queue_redraw()

func release() -> void:
    finger = -1
    mouse_drag = false
    axis = Vector2.ZERO
    queue_redraw()

func _notification(what: int) -> void:
    if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
        release()
