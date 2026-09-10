class_name WayfarerController
extends CharacterBody3D
var input_axis := Vector2.ZERO
var enabled := true
var geometry: Dictionary = {}
var avatar: WayfarerAvatar
var networked := false
var authoritative_position := Vector3.ZERO
var has_snapshot := false

func _ready() -> void:
    var shape = CapsuleShape3D.new()
    shape.radius = .35
    shape.height = 1.8
    var collision = CollisionShape3D.new()
    collision.shape = shape
    collision.position.y = .9
    add_child(collision)
    floor_snap_length = .35
    floor_max_angle = deg_to_rad(42)

func setup(appearance: Dictionary, zone_geometry: Dictionary) -> void:
    geometry = zone_geometry
    avatar = WayfarerAvatar.new()
    add_child(avatar)
    avatar.build(appearance)

func _physics_process(delta: float) -> void:
    var axis = input_axis if enabled else Vector2.ZERO
    var acceleration = geometry.get("acceleration", 16.0) if axis.length() > .01 else geometry.get("deceleration", 24.0)
    velocity.x = move_toward(velocity.x, axis.x * geometry.get("speed", 4.8), acceleration*delta)
    velocity.z = move_toward(velocity.z, axis.y * geometry.get("speed", 4.8), acceleration*delta)
    if not is_on_floor():
        velocity.y -= 24*delta
    move_and_slide()
    var bounds = geometry.get("bounds", [-24,-22,24,20])
    position.x = clampf(position.x, bounds[0]+.35, bounds[2]-.35)
    position.z = clampf(position.z, bounds[1]+.35, bounds[3]-.35)
    if networked and has_snapshot:
        var error = Vector2(position.x-authoritative_position.x, position.z-authoritative_position.z).length()
        if error > 2.0:
            position.x = authoritative_position.x
            position.z = authoritative_position.z
        elif error > .55:
            position.x = lerpf(position.x, authoritative_position.x, delta*4)
            position.z = lerpf(position.z, authoritative_position.z, delta*4)
    if avatar:
        avatar.travel_speed = Vector2(velocity.x,velocity.z).length()
        avatar.walking = Vector2(velocity.x, velocity.z).length() > .1
        if avatar.walking:
            avatar.rotation.y = lerp_angle(avatar.rotation.y, atan2(-velocity.x, -velocity.z), delta*12)

func reconcile(at: Vector3) -> void:
    authoritative_position = at
    if not has_snapshot:
        position.x = at.x
        position.z = at.z
    has_snapshot = true
