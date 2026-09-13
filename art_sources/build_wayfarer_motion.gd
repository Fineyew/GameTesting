extends SceneTree
## Original editable motion recipe. Run with Godot 4.5.1 after importing the GLBs:
## godot --headless --path godot_project --script ../art_sources/build_wayfarer_motion.gd
## The Blender rig/geometry and original Idle/Cast remain unchanged.
const DESTINATION = "res://assets/dawnreef/wayfarer_motion.tres"
const CLIPS = {"Walk":.72,"Run":.52,"TurnLeft":.48,"TurnRight":.48,"Hit":.20,"Recovery":.36}
var skeleton: Skeleton3D

func _init() -> void:
    call_deferred("build")

func rotate(pose: Dictionary, name: String, angle: float, axis := Vector3.RIGHT) -> void:
    var index = skeleton.find_bone(name)
    var parent = skeleton.get_bone_parent(index)
    var parent_basis = skeleton.get_bone_global_rest(parent).basis if parent >= 0 else Basis.IDENTITY
    pose[name] = parent_basis.inverse()*Basis(axis,angle)*skeleton.get_bone_global_rest(index).basis

func leg(pose: Dictionary, side: String, pelvis: Vector3, ankle: Vector3) -> void:
    var thigh = skeleton.find_bone("Thigh"+side)
    var shin = skeleton.find_bone("Shin"+side)
    var foot = skeleton.find_bone("Foot"+side)
    var hip = pelvis+skeleton.get_bone_rest(thigh).origin
    var rest_hip = skeleton.get_bone_global_rest(thigh)
    var rest_knee = skeleton.get_bone_global_rest(shin)
    var rest_ankle = skeleton.get_bone_global_rest(foot)
    var upper = rest_hip.origin.distance_to(rest_knee.origin)
    var lower = rest_knee.origin.distance_to(rest_ankle.origin)
    var offset = ankle-hip
    var distance = clampf(offset.length(),.05,upper+lower-.001)
    var direction = offset.normalized()
    var forward = (Vector3.FORWARD-direction*Vector3.FORWARD.dot(direction)).normalized()
    var along = (upper*upper-lower*lower+distance*distance)/(2*distance)
    var knee = hip+direction*along+forward*sqrt(maxf(0,upper*upper-along*along))
    var upper_basis = Basis(Quaternion((rest_knee.origin-rest_hip.origin).normalized(),(knee-hip).normalized()))*rest_hip.basis
    var lower_basis = Basis(Quaternion((rest_ankle.origin-rest_knee.origin).normalized(),(ankle-knee).normalized()))*rest_knee.basis
    pose["Thigh"+side] = upper_basis
    pose["Shin"+side] = upper_basis.inverse()*lower_basis
    # Keep each sole level during contact; swing clearance comes from the knee.
    pose["Foot"+side] = lower_basis.inverse()*rest_ankle.basis

func build() -> void:
    var model = load("res://assets/dawnreef/wayfarer.glb").instantiate()
    root.add_child(model)
    skeleton = model.find_child("Skeleton3D",true,false)
    var library = AnimationLibrary.new()
    for clip in CLIPS:
        var animation = Animation.new()
        animation.length = CLIPS[clip]
        animation.loop_mode = Animation.LOOP_LINEAR if clip in ["Walk","Run","TurnLeft","TurnRight"] else Animation.LOOP_NONE
        for index in skeleton.get_bone_count():
            for kind in [Animation.TYPE_POSITION_3D,Animation.TYPE_ROTATION_3D]:
                var track = animation.add_track(kind)
                animation.track_set_path(track,"WayfarerRig/Skeleton3D:"+skeleton.get_bone_name(index))
        var samples = int(ceil(animation.length*120))
        for frame in samples+1:
            var t = float(frame)/samples
            var phase = t*TAU
            var pelvis = Vector3(0,.76,0)
            var pose: Dictionary = {}
            for index in skeleton.get_bone_count():
                pose[skeleton.get_bone_name(index)] = skeleton.get_bone_rest(index).basis
            if clip in ["Walk","Run"]:
                var running = clip == "Run"
                var duty = .33 if running else .52
                var reference_speed = 4.0 if running else 1.8
                var stride = reference_speed*animation.length*duty
                pelvis.y = .63+(.025 if running else .008)*sin(phase*2)
                for side in ["L","R"]:
                    var u = fmod(t+(0 if side == "L" else .5),1.0)
                    var z: float
                    var lift := 0.0
                    if u <= duty:
                        z = lerpf(-stride/2,stride/2,u/duty)
                    else:
                        var swing = (u-duty)/(1-duty)
                        z = cos(swing*PI)*stride/2
                        lift = (.28 if running else .11)*pow(sin(swing*PI),2)
                    leg(pose,side,pelvis,Vector3(-.13 if side == "L" else .13,.135+lift,.005+z))
                    var arm_swing = sin(phase+(0 if side == "L" else PI))
                    rotate(pose,"UpperArm"+side,arm_swing*(.18 if side == "L" else .48))
                    rotate(pose,"ForeArm"+side,(.40 if running else .12) if side == "L" else (.85 if running else .25))
                rotate(pose,"Chest",-.10 if running else -.025)
                rotate(pose,"Head",.06 if running else .015)
            elif clip.begins_with("Turn"):
                var sign = 1.0 if clip == "TurnLeft" else -1.0
                pelvis.y = .66
                rotate(pose,"Chest",sign*.09*sin(phase),Vector3.UP)
                for side in ["L","R"]:
                    var u = phase+(0 if side == "L" else PI)
                    leg(pose,side,pelvis,Vector3(-.13 if side == "L" else .13,.135+.06*maxf(0,sin(u)),.005+sign*.06*cos(u)))
            else:
                var weight = sin(t*PI/2) if clip == "Hit" else cos(t*PI/2)
                pelvis.y -= .10*weight
                rotate(pose,"Chest",.20*weight)
                rotate(pose,"Head",-.12*weight)
                rotate(pose,"UpperArmR",.28*weight)
                rotate(pose,"ForeArmR",.45*weight)
                for side in ["L","R"]:
                    leg(pose,side,pelvis,Vector3(-.13 if side == "L" else .13,.135,.005))
            for index in skeleton.get_bone_count():
                var name = skeleton.get_bone_name(index)
                animation.track_insert_key(index*2,t*animation.length,pelvis if name == "Pelvis" else skeleton.get_bone_rest(index).origin)
                animation.track_insert_key(index*2+1,t*animation.length,pose[name].get_rotation_quaternion())
        library.add_animation(clip,animation)
    assert(ResourceSaver.save(library,DESTINATION) == OK)
    model.free()
    print("WAYFARER_MOTION_AUTHORED: ",library.get_animation_list())
    quit()
