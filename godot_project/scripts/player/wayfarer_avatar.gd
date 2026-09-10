class_name WayfarerAvatar
extends Node3D
## Existing controller/presence interface; art and motion live in imported scenes.
const WAYFARER = preload("res://assets/dawnreef/wayfarer.glb")
const MARA = preload("res://assets/dawnreef/mara.glb")
static var appearance_materials: Dictionary = {}
var walking := false
var travel_speed := 2.0
var animation: AnimationPlayer
var cast_remaining := 0.0

func build(appearance: Dictionary, is_mara := false) -> void:
    var model = (MARA if is_mara else WAYFARER).instantiate()
    add_child(model)
    var robe = Color({"teal":"287d7e","coral":"c66a61","indigo":"665997"}.get(appearance.get("robe","teal"),"287d7e"))
    var skin = Color({"warm":"c38d65","deep":"795443","pale":"e3baa0"}.get(appearance.get("skin","warm"),"c38d65"))
    # Only per-character tint materials are duplicated; common accessories stay shared.
    for part in model.find_children("*","MeshInstance3D",true,false):
        for index in part.mesh.get_surface_count():
            var source = part.get_active_material(index)
            if source.resource_name == "RobeTint" or source.resource_name == "SkinTint":
                var color = robe if source.resource_name == "RobeTint" else skin
                var key = source.resource_name + color.to_html()
                if not appearance_materials.has(key):
                    var tint = source.duplicate() as StandardMaterial3D
                    tint.albedo_color = color
                    appearance_materials[key] = tint
                part.set_surface_override_material(index,appearance_materials[key])
    animation = model.find_child("AnimationPlayer",true,false)
    assert(animation != null,"Wayfarer art must include its authored animation player")
    for clip in ["Idle","Walk","Cast"]:
        assert(animation.has_animation(clip),"Missing Wayfarer animation " + clip)
    for clip in ["Idle","Walk"]:
        animation.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
    animation.play("Idle")
    ReefKit.contact_shadow(self,Vector3(0,.088,0),Vector2(1.25,.85))

func play_cast() -> void:
    cast_remaining = animation.get_animation("Cast").length
    animation.speed_scale = 1
    animation.play("Cast",.12)

func _process(delta: float) -> void:
    if animation == null:
        return
    if cast_remaining > 0:
        cast_remaining -= delta
        return
    var wanted = "Walk" if walking else "Idle"
    if animation.current_animation != wanted:
        animation.play(wanted,.16)
    animation.speed_scale = clampf(travel_speed/2.0,.4,2.7) if walking else 1.0
