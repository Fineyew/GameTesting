class_name TidebeatEffect
extends Node3D
## Bounded opaque geometry. This node never changes combat state or sends commands.
signal impact
signal finished
const PROFILES = {
    "prism_needle":["Lanterncraft","enemy",1.05,"cast","impact"],
    "reed_stitch":["Rootbinding","self",1.10,"root_cast","mend"],
    "stillwater_knot":["Tideseaming","enemy",1.15,"tide_cast","guard"],
    "glimmer_spark":["Lanterncraft","enemy",1.15,"cast","impact"],
    "beacon_trace":["Lanterncraft","enemy",.95,"cast","discovery"],
    "root_snare":["Rootbinding","enemy",1.10,"root_cast","guard"],
    "reed_aegis":["Rootbinding","self",1.05,"root_cast","guard"],
    "tide_mend":["Tideseaming","self",1.20,"tide_cast","mend"],
    "seam_lance":["Tideseaming","enemy",1.25,"tide_cast","impact"],
    "brace":["Wayfarer","self",.80,"guard","guard"],
    "gather":["Wayfarer","self",.95,"cast","mend"]}
const MAX_MESHES = 16
var action := ""
var elapsed := 0.0
var duration := 1.0
var reduced := false
var struck := false
var ended := false
var origin: Vector3
var target: Vector3
var pieces: Array[MeshInstance3D] = []
var emitter: MeshInstance3D
var projectile: MeshInstance3D
var core: Node3D

func configure(key: String, from: Vector3, to: Vector3, less_motion := false, speed := 1.0) -> void:
    assert(PROFILES.has(key))
    action = key
    origin = from
    target = to
    reduced = less_motion
    duration = float(PROFILES[key][2])/clampf(speed,1.0,3.0)
    var family = PROFILES[key][0]
    var color = Color("ffdda0") if family == "Lanterncraft" else (Color("98dda8") if family == "Rootbinding" else Color("9bdef0"))
    var center = origin if PROFILES[key][1] == "self" else target
    core = Node3D.new()
    add_child(core)
    core.position = center
    emitter = ring(self,origin,.24,color)
    emitter.rotation.x = PI/2
    match key:
        "prism_needle":
            stem(self,origin,target,.022,color)
            for i in 3:
                var ray = box(core,Vector3(.05,.52,.05),Vector3((i-1)*.2,0,0),color)
                ray.rotation.z = (i-1)*.5
        "reed_stitch":
            for i in 4:
                var stitch = box(core,Vector3(.07,.72,.07),Vector3((i-1.5)*.18,0,0),color)
                stitch.rotation.z = .45 if i%2 else -.45
            ring(core,Vector3(0,-.6,0),.55,color)
            box(core,Vector3(.08,.34,.08),Vector3(0,.62,0),color)
            box(core,Vector3(.3,.08,.08),Vector3(0,.62,0),color)
        "stillwater_knot":
            for i in [-1,1]:
                var knot = ring(core,Vector3(i*.2,0,0),.3,color)
                knot.rotation.x = PI/2
                knot.rotation.z = i*.4
            ring(self,origin-Vector3.UP*.7,.45,color)
            stem(self,origin,target,.018,color)
        "glimmer_spark":
            projectile = shape(self,SphereMesh.new(),origin,color)
            projectile.mesh.radius = .10
            projectile.mesh.height = .20
            projectile.mesh.radial_segments = 10
            projectile.mesh.rings = 4
            ring(core,Vector3.ZERO,.65,color).rotation.x = PI/2
            for i in 8:
                var shard = box(core,Vector3(.055,.23,.055),Vector3(cos(i*TAU/8),sin(i*TAU/8),0)*.7,color)
                shard.rotation.z = -i*TAU/8
        "beacon_trace":
            ring(core,Vector3.ZERO,.62,color).rotation.x = PI/2
            for i in 4:
                var vane = box(core,Vector3(.06,.45,.06),Vector3(cos(i*PI/2),sin(i*PI/2),0)*.85,color)
                vane.rotation.z = PI/2-i*PI/2
            box(core,Vector3(.20,.20,.09),Vector3.ZERO,color).rotation.z = PI/4
        "root_snare":
            for i in 5:
                var angle = i*TAU/5
                var base = Vector3(cos(angle),-.9,sin(angle))*.9
                var top = Vector3(cos(angle+.6)*.35,.3,sin(angle+.6)*.35)
                stem(core,base,base.lerp(top,.5)+Vector3.UP*.15,.07,color)
                stem(core,base.lerp(top,.5)+Vector3.UP*.15,top,.055,color)
        "reed_aegis":
            for i in 7:
                var at = Vector3((i-3)*.16,0,-.6)
                box(core,Vector3(.10,.9-abs(i-3)*.10,.08),at,color).rotation.z = (i-3)*-.12
            for y in [-.24,.05,.27]:
                box(core,Vector3(1.18,.065,.1),Vector3(0,y,-.65),color)
        "tide_mend":
            for i in 3:
                ring(core,Vector3(0,(i-1)*.35,0),.55+i*.09,color)
            box(core,Vector3(.10,.55,.10),Vector3(0,.65,0),color)
            box(core,Vector3(.42,.10,.10),Vector3(0,.65,0),color)
        "seam_lance":
            var line = origin.direction_to(target)
            var side = line.cross(Vector3.UP).normalized()*.14
            for offset in [-side,side]:
                stem(self,origin+offset,target+offset,.04,color)
            for i in 3:
                var slash = box(core,Vector3(.055,.85,.055),Vector3((i-1)*.24,0,0),color)
                slash.rotation.z = -.5
        "brace":
            for angle in [-.75,.75]:
                box(core,Vector3(.11,1.1,.09),Vector3(0,0,-.55),Color("f3ead5")).rotation.z = angle
            ring(core,Vector3(0,-.8,0),.6,Color("f3ead5"))
        "gather":
            ring(core,Vector3(0,-.65,0),.65,color)
            for i in 6:
                var mote = box(core,Vector3(.11,.11,.11),Vector3(cos(i*TAU/6)*.7,.15,sin(i*TAU/6)*.7),color)
                mote.rotation.z = PI/4
    assert(pieces.size() <= MAX_MESHES)
    update_pose(0)

func shape(parent: Node3D, mesh: Mesh, at: Vector3, color: Color) -> MeshInstance3D:
    var node = ReefKit.mesh(parent,mesh,at,color,true)
    node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    pieces.append(node)
    return node

func box(parent: Node3D, size: Vector3, at: Vector3, color: Color) -> MeshInstance3D:
    var mesh = BoxMesh.new()
    mesh.size = size
    return shape(parent,mesh,at,color)

func ring(parent: Node3D, at: Vector3, radius: float, color: Color) -> MeshInstance3D:
    var mesh = TorusMesh.new()
    mesh.inner_radius = radius-.035
    mesh.outer_radius = radius+.035
    mesh.rings = 24
    mesh.ring_segments = 4
    return shape(parent,mesh,at,color)

func stem(parent: Node3D, from: Vector3, to: Vector3, radius: float, color: Color) -> void:
    var mesh = CylinderMesh.new()
    mesh.bottom_radius = radius
    mesh.top_radius = radius*.55
    mesh.height = from.distance_to(to)
    mesh.radial_segments = 6
    mesh.rings = 1
    var node = shape(parent,mesh,from.lerp(to,.5),color)
    node.quaternion = Quaternion(Vector3.UP,from.direction_to(to))

func update_pose(progress: float) -> void:
    if reduced:
        # The final silhouette stays still; essential geometry is never removed.
        emitter.visible = false
        if projectile:
            projectile.position = target
        return
    var anticipation = clampf(progress/.28,0,1)
    var travel = clampf((progress-.23)/.32,0,1)
    var release = clampf((progress-.55)/.45,0,1)
    emitter.scale = Vector3.ONE*(.5+anticipation*.9)*(1-release)
    emitter.rotation.z = anticipation*.7
    core.visible = progress >= .28
    var spread = .55+.45*clampf((progress-.28)/.27,0,1)
    core.scale = Vector3.ONE*spread*(1-release*.7)
    if action == "root_snare":
        core.position.y = target.y-(1-spread)*.8
    elif action == "tide_mend":
        core.position.y = origin.y+release*.22
    elif action == "gather":
        core.scale = Vector3.ONE*(1-release*.65)
    if projectile:
        projectile.position = origin.lerp(target,travel)+Vector3.UP*sin(travel*PI)*.35
        projectile.scale = Vector3.ONE*(1-release)
    if action == "prism_needle":
        pieces[1].visible = progress >= .28
    if action == "stillwater_knot":
        pieces[4].visible = progress >= .28
    if action == "seam_lance":
        for i in [1,2]:
            pieces[i].visible = progress >= .28 and progress < .72

func _process(delta: float) -> void:
    if ended:
        return
    elapsed += delta
    update_pose(clampf(elapsed/duration,0,1))
    if elapsed >= duration*.55 and not struck:
        struck = true
        impact.emit()
    if elapsed >= duration:
        finish()

func finish() -> void:
    if ended:
        return
    ended = true
    hide()
    finished.emit()
    queue_free()
