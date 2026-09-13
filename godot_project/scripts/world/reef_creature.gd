class_name ReefCreature
extends Node3D
## Original small reef silhouettes, animated in place without gameplay authority.
@export var creature_key := "shellfold_sifter"
var plates: Array[Node3D] = []
var fins: Array[Node3D] = []
var phase := 0.0
var guarded := false
var drawing_focus := false

func _ready() -> void:
    if creature_key == "shellfold_sifter":
        build_sifter()
    else:
        build_ray()
    ReefKit.label(self,GameData.display_name("enemies",creature_key),Vector3(0,2.0,0))

func polygon(parent: Node3D, vertices: Array, color: Color) -> MeshInstance3D:
    var surface = SurfaceTool.new()
    surface.begin(Mesh.PRIMITIVE_TRIANGLES)
    for vertex in vertices:
        surface.add_vertex(vertex)
    surface.generate_normals()
    var node = ReefKit.mesh(parent,surface.commit(),Vector3.ZERO,color)
    return node

func build_sifter() -> void:
    var body = ReefKit.sphere(self,.45,Vector3(0,.43,0),Color("b58365"))
    body.scale = Vector3(1.2,.65,1.0)
    for i in 5:
        var hinge = Node3D.new()
        add_child(hinge)
        hinge.position = Vector3(0,.52,.3)
        hinge.rotation.y = (i-2)*.30
        var root = Vector3(-.14,0,0)
        var tip = Vector3(0,.62,-.85)
        var edge = Vector3(.14,0,0)
        var back = Vector3(0,.16,-1.0)
        polygon(hinge,[root,tip,edge,root,back,tip,tip,back,edge,edge,back,root],Color("d6a67e") if i%2 else Color("597f84"))
        plates.append(hinge)
    for side in [-1,1]:
        for z in [-.22,.18,.48]:
            var leg = ReefKit.box(self,Vector3(.45,.09,.09),Vector3(side*.5,.19,z),Color("77543f"))
            leg.rotation.z = side*-.22
        ReefKit.sphere(self,.065,Vector3(side*.19,.54,.44),Color("f4d3a0"),true)

func build_ray() -> void:
    var body = ReefKit.sphere(self,.32,Vector3(0,.9,0),Color("577d99"))
    body.scale = Vector3(1,.48,1.8)
    for side in [-1,1]:
        var fin = Node3D.new()
        add_child(fin)
        fin.position.y = .9
        var a = Vector3(side*.12,0,.45)
        var b = Vector3(side*1.0,-.08,-.12)
        var c = Vector3(side*.13,0,-.62)
        var d = Vector3(side*.43,.14,-.15)
        polygon(fin,[a,b,d,b,c,d,c,a,d,d,b,a,d,c,b,d,a,c],Color("97bfd0"))
        var vein = ReefKit.box(fin,Vector3(.72,.035,.04),Vector3(side*.45,.04,-.1),Color("e5d197"))
        vein.rotation.z = side*-.12
        fins.append(fin)
        ReefKit.sphere(self,.06,Vector3(side*.12,.98,.38),Color("eedba7"),true)
    var tail = ReefKit.box(self,Vector3(.06,.05,.85),Vector3(0,.86,-.84),Color("577d99"))
    tail.rotation.x = -.18

func set_intent(intent: Dictionary) -> void:
    guarded = int(intent.get("guard",0)) > 0
    drawing_focus = int(intent.get("focus_drain",0)) > 0

func _process(delta: float) -> void:
    phase += delta
    for i in plates.size():
        var angle = -.06 if guarded else -.45+absf(i-2)*.07
        plates[i].rotation.x = lerpf(plates[i].rotation.x,angle,1-exp(-6*delta))
    for i in fins.size():
        fins[i].rotation.z = sin(phase*(3 if drawing_focus else 1.7))*.10*(1 if i else -1)
