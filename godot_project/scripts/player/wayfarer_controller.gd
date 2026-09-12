class_name WayfarerController
extends CharacterBody3D
var input_axis := Vector2.ZERO
var enabled := true
var geometry: Dictionary = {}
var avatar: WayfarerAvatar
var networked := false
var authoritative_position := Vector3.ZERO
var has_snapshot := false
var terrain: TerrainSurface

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
    if geometry.has("terrain"):
        terrain = TerrainSurface.new()
        var terrain_error = terrain.configure(geometry.terrain)
        if not terrain_error.is_empty():
            push_error(terrain_error)
            set_physics_process(false)
            return
    avatar = WayfarerAvatar.new()
    add_child(avatar)
    avatar.build(appearance)

func _physics_process(delta: float) -> void:
    var axis = input_axis if enabled else Vector2.ZERO
    var acceleration = geometry.get("acceleration", 16.0) if axis.length() > .01 else geometry.get("deceleration", 24.0)
    velocity.x = move_toward(velocity.x, axis.x * geometry.get("speed", 4.8), acceleration*delta)
    velocity.z = move_toward(velocity.z, axis.y * geometry.get("speed", 4.8), acceleration*delta)
    if terrain:
        var motion = TerrainTraversal.move(terrain,Vector2(position.x,position.z),Vector2(velocity.x,velocity.z)*minf(delta,.1),geometry.blockers)
        position.x = motion.position.x
        position.z = motion.position.y
        if motion.stopped[0]: velocity.x = 0
        if motion.stopped[1]: velocity.z = 0
        velocity.y = 0
        if networked and has_snapshot:
            var distance = Vector2(position.x-authoritative_position.x,position.z-authoritative_position.z).length()
            if distance > 2:
                position = authoritative_position
            elif distance > .55:
                var correction = Vector2(authoritative_position.x-position.x,authoritative_position.z-position.z)*minf(1,delta*4)
                var settled = TerrainTraversal.move(terrain,Vector2(position.x,position.z),correction.limit_length(1),geometry.blockers)
                position.x = settled.position.x
                position.z = settled.position.y
        var floor_state = terrain.sample(position.x,position.z)
        if not floor_state.is_empty(): position.y = floor_state.height
    else:
        if not is_on_floor(): velocity.y -= 24*delta
        move_and_slide()
        var bounds = geometry.get("bounds", [-24,-22,24,20])
        position.x = clampf(position.x,bounds[0]+.35,bounds[2]-.35)
        position.z = clampf(position.z,bounds[1]+.35,bounds[3]-.35)
        if networked and has_snapshot:
            var error = Vector2(position.x-authoritative_position.x,position.z-authoritative_position.z).length()
            if error > 2:
                position.x = authoritative_position.x
                position.z = authoritative_position.z
            elif error > .55:
                position.x = lerpf(position.x,authoritative_position.x,delta*4)
                position.z = lerpf(position.z,authoritative_position.z,delta*4)
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
        position.y = at.y
    has_snapshot = true
