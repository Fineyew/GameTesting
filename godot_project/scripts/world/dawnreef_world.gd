class_name DawnreefWorld
extends Node3D
var geometry: Dictionary
var sun: DirectionalLight3D
var well_light: MeshInstance3D
var enemy: Node3D
var elapsed := 0.0

func _ready() -> void:
    geometry = GameData.definition("zones", "dawnreef_atoll").rules.world
    _environment()
    _landscape()
    for blocker in geometry.blockers:
        _house(blocker)
    _landmarks()
    ReefKit.batch_static(self, [well_light])

func _environment() -> void:
    var sky_material = ProceduralSkyMaterial.new()
    sky_material.sky_top_color = Color("365f7f")
    sky_material.sky_horizon_color = Color("b0d4cd")
    sky_material.ground_horizon_color = Color("b0d4cd")
    sky_material.ground_bottom_color = Color("255868")
    var sky = Sky.new()
    sky.sky_material = sky_material
    var environment = Environment.new()
    environment.background_mode = Environment.BG_SKY
    environment.sky = sky
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color("a6ccc2")
    environment.ambient_light_energy = .35
    environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
    var world_environment = WorldEnvironment.new()
    world_environment.environment = environment
    add_child(world_environment)
    sun = DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-48,-32,0)
    sun.light_color = Color("fff0c9")
    sun.light_energy = .9
    sun.shadow_enabled = false
    sun.directional_shadow_max_distance = 55
    add_child(sun)

func _landscape() -> void:
    ReefKit.box(self,Vector3(48,.8,42),Vector3(0,-.4,-1),Color("709881"),true)
    ReefKit.box(self,Vector3(450,.2,450),Vector3(0,-1.5,0),Color("357a8d"))
    ReefKit.box(self,Vector3(5,.04,40),Vector3(0,.02,-1),Color("d4c295"))
    ReefKit.box(self,Vector3(42,.04,3.5),Vector3(0,.025,-4),Color("d4c295"))
    for i in 10:
        var angle = i*TAU/10
        ReefKit.cylinder(self,7,4,Vector3(cos(angle)*20,-2,sin(angle)*18-1),Color("857b68"),5)
    for i in 8:
        var angle = i*TAU/8
        var at = Vector3(cos(angle)*85,-4+sin(i)*4,sin(angle)*78)
        ReefKit.cylinder(self,13,12,at,Color("638b8b"),7)
        ReefKit.cylinder(self,7,1,at+Vector3.UP*6,Color("75a29a"),8)
        ReefKit.cylinder(self,3,16,at+Vector3(0,14,0),Color("79a3a2"),.5)
    var random = RandomNumberGenerator.new()
    random.seed = 4096
    for i in 28:
        var at = Vector3(random.randf_range(-22,22),0,random.randf_range(-20,17))
        if absf(at.x) < 4 or absf(at.z+4)<3 or _inside_building(at):
            continue
        ReefKit.cylinder(self,.24,2.6,at+Vector3.UP*1.3,Color("74624f"),.17)
        var crown = ReefKit.sphere(self,1.5,at+Vector3.UP*3.1,Color("417e78"))
        crown.scale = Vector3(1,.65,1)
        ReefKit.sphere(self,.7,at+Vector3(.8,3.25,0),Color("71a89b"))
    for i in 12:
        var at = Vector3(-9+sin(i*2)*1.1,.6,-14+cos(i*3)*.8)
        ReefKit.cylinder(self,.07,1.2,at,Color("dbb866"),.03)
        ReefKit.sphere(self,.12,at+Vector3.UP*.6,Color("ebcb77"),true)

func _inside_building(at: Vector3) -> bool:
    for b in geometry.blockers:
        if b[0]-2 < at.x and at.x < b[2]+2 and b[1]-2 < at.z and at.z < b[3]+2:
            return true
    return false

func _house(bounds: Array) -> void:
    var width = bounds[2]-bounds[0]
    var depth = bounds[3]-bounds[1]
    var at = Vector3((bounds[0]+bounds[2])/2,0,(bounds[1]+bounds[3])/2)
    ReefKit.box(self,Vector3(width,3.6,depth),at+Vector3.UP*1.8,Color("d4c29f"),true)
    var roof = PrismMesh.new()
    roof.size = Vector3(width+1,2.3,depth+1)
    ReefKit.mesh(self,roof,at+Vector3.UP*4.7,Color("416d7e"))
    ReefKit.box(self,Vector3(1.3,2.2,.1),at+Vector3(0,1.1,depth/2+.06),Color("705947"))
    for x in [-width*.3,width*.3]:
        ReefKit.box(self,Vector3(1.05,1.2,.12),at+Vector3(x,2.05,depth/2+.1),Color("ddbb6e"))
        ReefKit.box(self,Vector3(1.25,.13,.2),at+Vector3(x,1.4,depth/2+.13),Color("476a69"))
    ReefKit.box(self,Vector3(.7,2,.7),at+Vector3(width*.3,5,0),Color("b3a285"))

func _landmarks() -> void:
    ReefKit.cylinder(self,1.3,.5,Vector3(0,.25,-5),Color("b7ac90"))
    ReefKit.cylinder(self,1.05,.6,Vector3(0,.6,-5),Color("6e8d8b"),.9)
    well_light = ReefKit.sphere(self,.38,Vector3(0,1.5,-5),Color("d7da87"),true)
    for x in [-1.5,1.5]:
        ReefKit.cylinder(self,.13,3.2,Vector3(x,1.6,-5),Color("a69778"))
    ReefKit.box(self,Vector3(3.6,.22,.4),Vector3(0,3.2,-5),Color("a69778"))
    ReefKit.label(self,"LANTERN WELL",Vector3(0,3.65,-5))
    var mara = WayfarerAvatar.new()
    add_child(mara)
    mara.position = Vector3(-4,0,-4)
    mara.build({"robe":"coral","skin":"deep"})
    ReefKit.label(mara,"Mara Lanternwright",Vector3(0,2.3,0))
    enemy = Node3D.new()
    add_child(enemy)
    enemy.position = Vector3(12,0,-10)
    ReefKit.sphere(enemy,.65,Vector3(0,.72,0),Color("685270"))
    for i in 7:
        var angle = i*TAU/7
        var thorn = ReefKit.cylinder(enemy,.18,.9,Vector3(sin(angle)*.5,1,cos(angle)*.5),Color("514658"),0)
        thorn.rotation.z = sin(angle)*.7
    for x in [-.23,.23]:
        ReefKit.sphere(enemy,.1,Vector3(x,.85,.57),Color("e3bf6e"),true)
    ReefKit.label(enemy,"Fog-Thorn Lurker",Vector3(0,2.1,0))
    for x in [16.4,19.6]:
        ReefKit.box(self,Vector3(.8,4,.8),Vector3(x,2,-18),Color("8d9d92"))
    ReefKit.box(self,Vector3(4,1,1),Vector3(18,4.2,-18),Color("8d9d92"))
    ReefKit.label(self,"SALTGLASS CISTERN",Vector3(18,5,-18))
    ReefKit.label(self,"Sunthread reeds",Vector3(-9,2.4,-14))
    for i in 5:
        ReefKit.box(self,Vector3(4,.25,1.2),Vector3(0,.12,17+i*1.1),Color("8a7556"))

func _process(delta: float) -> void:
    elapsed += delta
    well_light.position.y = 1.5 + sin(elapsed*1.8)*.1

func spell_impact(spell: String) -> void:
    var heal = spell == "tide_mend" or spell == "reed_aegis"
    var at = Vector3(0,1,-5) if heal else Vector3(12,1,-10)
    var burst = ReefKit.sphere(self,.15,at,Color("85d7be") if heal else Color("f2c676"),true)
    var tween = create_tween()
    tween.tween_property(burst,"scale",Vector3.ONE*8,.28)
    tween.tween_property(burst,"scale",Vector3.ZERO,.3)
    tween.tween_callback(burst.queue_free)
    if not heal:
        var reaction = create_tween()
        reaction.tween_property(enemy,"scale",Vector3(1.12,.8,1.12),.12)
        reaction.tween_property(enemy,"scale",Vector3.ONE,.3)
