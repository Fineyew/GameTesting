class_name WayfarerPreview
extends VBoxContainer
## One temporary, isolated stage; never joins the gameplay world or owns saved state.
var viewport: SubViewport
var avatar: WayfarerAvatar
var camera: Camera3D
var surface: SubViewportContainer
var turn_left: Button
var turn_right: Button
var reset_button: Button
var touch_index := -1
const FRONT := PI

func _ready() -> void:
    size_flags_horizontal = Control.SIZE_EXPAND_FILL
    size_flags_vertical = Control.SIZE_EXPAND_FILL
    var heading = TideUI.label("YOUR WAYFARER",18,TideUI.GOLD)
    heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    add_child(heading)
    surface = SubViewportContainer.new()
    surface.size_flags_vertical = Control.SIZE_EXPAND_FILL
    surface.custom_minimum_size = Vector2(220,180)
    surface.stretch = true
    surface.mouse_filter = Control.MOUSE_FILTER_STOP
    # Keep the panel as the mouse target; this stage contains no gameplay input.
    surface.mouse_target = true
    add_child(surface)
    viewport = SubViewport.new()
    viewport.own_world_3d = true
    viewport.gui_disable_input = true
    viewport.transparent_bg = true
    viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
    surface.add_child(viewport)
    var stage = Node3D.new()
    viewport.add_child(stage)
    var environment = WorldEnvironment.new()
    environment.environment = Environment.new()
    environment.environment.background_mode = Environment.BG_COLOR
    environment.environment.background_color = Color("163941")
    environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.environment.ambient_light_color = Color("e4e8dc")
    environment.environment.ambient_light_energy = .75
    stage.add_child(environment)
    var light = DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-35,-35,0)
    light.light_color = Color("fff0d9")
    light.light_energy = 1.05
    light.shadow_enabled = false
    stage.add_child(light)
    avatar = WayfarerAvatar.new()
    stage.add_child(avatar)
    avatar.build({})
    avatar.rotation.y = FRONT
    camera = Camera3D.new()
    stage.add_child(camera)
    camera.projection = Camera3D.PROJECTION_ORTHOGONAL
    camera.keep_aspect = Camera3D.KEEP_HEIGHT
    camera.position = Vector3(0,1.25,5)
    camera.look_at(Vector3(0,1.12,0))
    camera.current = true
    surface.resized.connect(_frame_avatar)
    surface.gui_input.connect(_preview_input)
    visibility_changed.connect(_visibility_changed)
    var controls = HBoxContainer.new()
    controls.alignment = BoxContainer.ALIGNMENT_CENTER
    add_child(controls)
    turn_left = TideUI.button("Left",func(): turn(-PI/4))
    reset_button = TideUI.button("Front",func(): avatar.rotation.y = FRONT)
    turn_right = TideUI.button("Right",func(): turn(PI/4))
    turn_left.tooltip_text = "Turn left"
    turn_right.tooltip_text = "Turn right"
    for button in [turn_left,reset_button,turn_right]:
        controls.add_child(button)
    var hint = TideUI.paragraph("Drag to rotate · Your colors carry into Dawnreef",16)
    hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    add_child(hint)
    _frame_avatar()

func set_appearance(appearance: Dictionary) -> void:
    avatar.apply_appearance(appearance)

func turn(radians: float) -> void:
    avatar.rotation.y = wrapf(avatar.rotation.y+radians,-PI,PI)

func _frame_avatar() -> void:
    if camera != null:
        # Fit both height and the staff/coat width, including a narrow tablet column.
        camera.size = maxf(2.7,2.5*surface.size.y/maxf(surface.size.x,1))

func _preview_input(event: InputEvent) -> void:
    if event is InputEventScreenTouch:
        if event.pressed and touch_index == -1:
            touch_index = event.index
        elif not event.pressed and touch_index == event.index:
            touch_index = -1
        surface.accept_event()
    elif event is InputEventScreenDrag and event.index == touch_index:
        turn(event.relative.x*.012)
        surface.accept_event()
    elif event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT) and touch_index == -1:
        turn(event.relative.x*.012)
        surface.accept_event()

func _visibility_changed() -> void:
    if viewport != null:
        viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS if is_visible_in_tree() else SubViewport.UPDATE_DISABLED
    touch_index = -1

func _notification(what: int) -> void:
    if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
        touch_index = -1
