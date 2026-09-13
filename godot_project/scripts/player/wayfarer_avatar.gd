class_name WayfarerAvatar
extends Node3D
signal footstep
## Existing controller/presence interface; art and motion live in imported scenes.
const WAYFARER = preload("res://assets/dawnreef/wayfarer.glb")
const MARA = preload("res://assets/dawnreef/mara.glb")
const WAYFARER_FAR = preload("res://assets/dawnreef/wayfarer_far.glb")
const MARA_FAR = preload("res://assets/dawnreef/mara_far.glb")
const MOTION = preload("res://assets/dawnreef/wayfarer_motion.tres")
static var appearance_materials: Dictionary = {}
var walking := false
var running := false
var turn_error := 0.0
var travel_speed := 0.0
var animation: AnimationPlayer
var cast_remaining := 0.0
var reaction_remaining := 0.0
var recovering := false
var gait_rate := 1.0
var model: Node3D
var body: MeshInstance3D
var near_mesh: Mesh
var near_skin: Skin
var far_mesh: Mesh
var far_skin: Skin
var distant := false
var current_appearance: Dictionary = {}
var step_clip := ""
var step_half := -1

func set_travel_velocity(motion: Vector3) -> void:
    # Animation follows horizontal travel, not stair height or pixels per frame.
    travel_speed = Vector2(motion.x,motion.z).length()
    # Separate enter/exit thresholds keep small snapshot tails from toggling clips.
    walking = travel_speed > (.08 if walking else .18)
    running = walking and travel_speed > (2.4 if running else 2.8)

func face_travel(heading: float, delta: float, response := 12.0) -> void:
    turn_error = angle_difference(rotation.y,heading)
    rotation.y = lerp_angle(rotation.y,heading,1.0-exp(-response*delta))

func build(appearance: Dictionary, is_mara := false) -> void:
    model = (MARA if is_mara else WAYFARER).instantiate()
    add_child(model)
    body = model.find_children("*","MeshInstance3D",true,false)[0]
    near_mesh = body.mesh
    near_skin = body.skin
    var low_model = (MARA_FAR if is_mara else WAYFARER_FAR).instantiate()
    var low_body = low_model.find_children("*","MeshInstance3D",true,false)[0]
    far_mesh = low_body.mesh
    far_skin = low_body.skin
    low_model.free()
    apply_appearance(appearance)
    animation = model.find_child("AnimationPlayer",true,false)
    assert(animation != null,"Wayfarer art must include its authored animation player")
    # Each player owns its mapping; immutable clips are shared across every rig.
    var clips = animation.get_animation_library("").duplicate() as AnimationLibrary
    for clip in MOTION.get_animation_list():
        if clips.has_animation(clip):
            clips.remove_animation(clip)
        clips.add_animation(clip,MOTION.get_animation(clip))
    animation.remove_animation_library("")
    animation.add_animation_library("",clips)
    for clip in ["Idle","Walk","Run","TurnLeft","TurnRight","Cast","Hit","Recovery"]:
        assert(animation.has_animation(clip),"Missing Wayfarer animation " + clip)
    for clip in ["Idle","Walk"]:
        animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
    animation.play("Idle")
    ReefKit.contact_shadow(self,Vector3(0,.088,0),Vector2(1.25,.85))

func follow_terrain(surface: TerrainSurface) -> void:
    var rig = model.find_child("Skeleton3D",true,false) as Skeleton3D
    var footing = WayfarerFooting.new()
    rig.add_child(footing)
    footing.configure(surface)

func apply_appearance(appearance: Dictionary) -> void:
    current_appearance = appearance.duplicate()
    # Creator and world share the same tint/fallback path without rebuilding rigs.
    var robe = Color({"teal":"287d7e","coral":"c66a61","indigo":"665997"}.get(appearance.get("robe","teal"),"287d7e"))
    var skin = Color({"warm":"c38d65","deep":"795443","pale":"e3baa0"}.get(appearance.get("skin","warm"),"c38d65"))
    # Only per-character tint materials are duplicated; common accessories stay shared.
    for part in model.find_children("*","MeshInstance3D",true,false):
        for index in part.mesh.get_surface_count():
            var source = part.mesh.surface_get_material(index)
            if source.resource_name == "RobeTint" or source.resource_name == "SkinTint":
                var color = robe if source.resource_name == "RobeTint" else skin
                var key = source.resource_name + color.to_html()
                if not appearance_materials.has(key):
                    var tint = source.duplicate() as StandardMaterial3D
                    tint.albedo_color = color
                    appearance_materials[key] = tint
                part.set_surface_override_material(index,appearance_materials[key])

func update_detail(distance: float) -> void:
    var wanted = distance > (7.5 if distant else 8.5)
    if wanted == distant:
        return
    distant = wanted
    body.mesh = far_mesh if distant else near_mesh
    body.skin = far_skin if distant else near_skin
    apply_appearance(current_appearance)

func play_cast(speed := 1.0) -> void:
    reaction_remaining = 0
    recovering = false
    cast_remaining = animation.get_animation("Cast").length/clampf(speed,1,3)
    animation.speed_scale = clampf(speed,1,3)
    animation.play("Cast",.12)

func play_hit(speed := 1.0) -> void:
    cast_remaining = 0
    recovering = false
    reaction_remaining = animation.get_animation("Hit").length/clampf(speed,1,3)
    animation.speed_scale = clampf(speed,1,3)
    animation.play("Hit",.04)

func play_recovery(speed := 1.0) -> void:
    cast_remaining = 0
    recovering = true
    reaction_remaining = animation.get_animation("Recovery").length/clampf(speed,1,3)
    animation.speed_scale = clampf(speed,1,3)
    animation.play("Recovery",.04)

func finish_action_pose() -> void:
    cast_remaining = 0
    reaction_remaining = 0
    recovering = false
    animation.speed_scale = 1
    animation.play("Idle",.08)

func _process(delta: float) -> void:
    if animation == null:
        return
    var viewer = get_viewport().get_camera_3d()
    if viewer:
        update_detail(viewer.global_position.distance_to(global_position))
    var current = animation.current_animation
    if current in ["Walk","Run"] and walking and travel_speed > .6:
        var half = int(floor(animation.current_animation_position/animation.current_animation_length*2))%2
        if step_clip == current and step_half != half:
            footstep.emit()
        step_clip = current
        step_half = half
    else:
        step_clip = ""
        step_half = -1
    var target_rate = clampf(travel_speed/(4.0 if running else 1.8),.4,2.0) if walking else 1.0
    gait_rate = lerpf(gait_rate,target_rate,1.0-exp(-12.0*delta))
    if cast_remaining > 0:
        cast_remaining -= delta
        return
    if reaction_remaining > 0:
        reaction_remaining -= delta
        if reaction_remaining <= 0 and not recovering:
            play_recovery()
        return
    var wanted = ("Run" if running else "Walk") if walking else "Idle"
    if walking and travel_speed < 1.0 and absf(turn_error) > .45:
        wanted = "TurnLeft" if turn_error > 0 else "TurnRight"
    if animation.current_animation != wanted:
        var cycle = -1.0
        if animation.current_animation in ["Walk","Run"] and wanted in ["Walk","Run"]:
            cycle = fmod(animation.current_animation_position/animation.current_animation_length,1.0)
        animation.play(wanted,.16)
        if cycle >= 0:
            animation.seek(cycle*animation.current_animation_length)
    animation.speed_scale = gait_rate if wanted in ["Walk","Run"] else 1.0
