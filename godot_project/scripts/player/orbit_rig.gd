class_name OrbitRig
extends Node3D
var target: Node3D
var arm: SpringArm3D
var camera: Camera3D
var yaw := 0.0
var pitch := -.27
var enabled := true
var finger := -1

func _ready() -> void:
    arm = SpringArm3D.new()
    arm.spring_length = 5.4
    arm.collision_mask = 3 # World solids plus camera-only foliage; no movement change.
    arm.margin = .22
    var shape = SphereShape3D.new()
    shape.radius = .2
    arm.shape = shape
    add_child(arm)
    camera = Camera3D.new()
    camera.fov = 62
    camera.near = .1
    camera.far = 240
    camera.current = true
    arm.add_child(camera)

func _process(_delta: float) -> void:
    if is_instance_valid(target):
        position = target.position + Vector3(0,1.35,0)
    rotation = Vector3(pitch,yaw,0)

func _unhandled_input(event: InputEvent) -> void:
    if not enabled:
        finger = -1
        return
    if event is InputEventScreenTouch:
        if event.pressed and event.position.x > get_viewport().get_visible_rect().size.x * .45:
            finger = event.index
        elif event.index == finger:
            finger = -1
    if event is InputEventScreenDrag and event.index == finger:
        orbit(event.relative)
    if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
        orbit(event.relative)

func orbit(motion: Vector2) -> void:
    yaw -= motion.x * .005
    pitch = clampf(pitch-motion.y*.004, -.85, -.06)

func recenter() -> void:
    yaw = 0
    pitch = -.27

static func pair_frame(world: World3D, origin: Vector3, target: Vector3, excluded: RID) -> Vector3:
    var flat = Vector3(target.x-origin.x,0,target.z-origin.z)
    var direction = flat.normalized() if flat.length() > .02 else Vector3.FORWARD
    var side = Vector3(-direction.z,0,direction.x)
    var middle = origin.lerp(target,.5)
    var candidates = [middle+side*5+Vector3.UP*2.2,middle-side*5+Vector3.UP*2.2,
        middle-direction*5+Vector3.UP*3.2,middle+direction*5+Vector3.UP*3.2,
        middle+side*2+Vector3.UP*6]
    for at in candidates:
        var clear := true
        for point in [origin,target]:
            var ray = PhysicsRayQueryParameters3D.create(at,point,3,[excluded])
            ray.hit_from_inside = true
            if not world.direct_space_state.intersect_ray(ray).is_empty():
                clear = false
        if clear:
            return at
    return Vector3.INF # Caller keeps the gameplay view when no clean framing exists.
