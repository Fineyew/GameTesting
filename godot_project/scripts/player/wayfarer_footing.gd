class_name WayfarerFooting
extends SkeletonModifier3D
## Presentation-only two-bone fitting against the same terrain as the controller.
## Neither avatar root position nor authoritative movement is modified.
var terrain: TerrainSurface
var legs: Array = []

func configure(surface: TerrainSurface) -> void:
    terrain = surface
    var rig = get_skeleton()
    for side in ["L","R"]:
        legs.append([rig.find_bone("Thigh"+side),rig.find_bone("Shin"+side),rig.find_bone("Foot"+side)])

func _process_modification() -> void:
    if terrain == null or legs.is_empty():
        return
    var rig = get_skeleton()
    var viewer = get_viewport().get_camera_3d()
    if viewer and viewer.global_position.distance_squared_to(rig.global_position) > 400:
        return # Distant rigs keep the inexpensive baked contact poses.
    var targets: Array[Vector3] = []
    var soles: Array[Basis] = []
    var lowering := 0.0
    var changed := false
    for bones in legs:
        var foot = rig.get_bone_global_pose(bones[2])
        var world_foot = rig.to_global(foot.origin)
        var floor = terrain.sample(world_foot.x,world_foot.z)
        var adjustment = 0.0 if floor.is_empty() else clampf(floor.height-rig.global_position.y,-.3,.3)
        changed = changed or absf(adjustment) > .001
        lowering = minf(lowering,adjustment)
        targets.append(foot.origin+Vector3.UP*adjustment)
        soles.append(foot.basis)
    if not changed:
        return
    var pelvis = rig.find_bone("Pelvis")
    var pelvis_pose = rig.get_bone_pose(pelvis)
    pelvis_pose.origin.y += lowering
    rig.set_bone_pose(pelvis,pelvis_pose)
    for index in legs.size():
        var bones = legs[index]
        var hip = rig.get_bone_global_pose(bones[0])
        var knee = rig.get_bone_global_pose(bones[1])
        var foot = rig.get_bone_global_pose(bones[2])
        var upper = hip.origin.distance_to(knee.origin)
        var lower = knee.origin.distance_to(foot.origin)
        var offset = targets[index]-hip.origin
        var distance = clampf(offset.length(),absf(upper-lower)+.001,upper+lower-.001)
        var direction = offset.normalized()
        var forward = (Vector3.FORWARD-direction*Vector3.FORWARD.dot(direction)).normalized()
        var along = (upper*upper-lower*lower+distance*distance)/(2*distance)
        var joint = hip.origin+direction*along+forward*sqrt(maxf(0,upper*upper-along*along))
        var goal = hip.origin+direction*distance
        var upper_basis = Basis(Quaternion((knee.origin-hip.origin).normalized(),(joint-hip.origin).normalized()))*hip.basis
        var lower_basis = Basis(Quaternion((foot.origin-knee.origin).normalized(),(goal-joint).normalized()))*knee.basis
        var parent_basis = rig.get_bone_global_pose(rig.get_bone_parent(bones[0])).basis
        rig.set_bone_pose_rotation(bones[0],(parent_basis.inverse()*upper_basis).get_rotation_quaternion())
        rig.set_bone_pose_rotation(bones[1],(upper_basis.inverse()*lower_basis).get_rotation_quaternion())
        rig.set_bone_pose_rotation(bones[2],(lower_basis.inverse()*soles[index]).get_rotation_quaternion())
