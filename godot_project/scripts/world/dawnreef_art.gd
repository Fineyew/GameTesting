class_name DawnreefArt
extends Node3D
## M1.4 benchmark only. Placement respects the unchanged catalog collision bounds.
## Editable sources: art_sources/dawnreef/*.blend and build_dawnreef.py.
const KIT = preload("res://assets/dawnreef/dawnreef_kit.glb")
var pieces: Dictionary = {}

func _ready() -> void:
    var library = KIT.instantiate()
    for child in library.get_children():
        if child is MeshInstance3D:
            pieces[child.name] = child.mesh
    library.free()
    place("LanternWell",Vector3(0,0,-5))
    # Existing first building: a shop room and covered front supply display.
    # Both remain inside its existing server/client rectangle [-18,-10,-10,-4].
    place("SailHouse",Vector3(-14,0,-8),Vector3(1,1,.66))
    place("SupplyCart",Vector3(-11.5,0,-4.92))
    for at in [Vector3(-17,.0,-4.7),Vector3(-10.6,0,-6.3),Vector3(-5.9,0,-5.7),Vector3(3.7,0,-6.2)]:
        place("Planter",at,Vector3.ONE*.85)
    for at in [Vector3(-6.6,0,-1.8),Vector3(3.8,0,-2),Vector3(3.8,0,-8.6)]:
        place("LanternPost",at)
    for spec in [[Vector3(-6.6,0,1.2),.92,.4],[Vector3(6.6,0,1.8),1.05,-.6],
            [Vector3(-6.5,0,-8.7),1.12,.8],[Vector3(6.7,0,-9.1),.93,1.8]]:
        place("WindTree",spec[0],Vector3.ONE*spec[1],spec[2])
        ReefKit.contact_shadow(self,spec[0]+Vector3.UP*.055,Vector2(3.8,3.1)*spec[1])
    for i in 24:
        var angle = i*TAU/24
        place("PavingStone",Vector3(cos(angle)*2.15,.052,-5+sin(angle)*2.15),Vector3.ONE,angle)
    # Broken-in paving follows the existing path; no walkable ledges or new collision.
    for row in 12:
        for side in [-1,1]:
            place("PavingStone",Vector3(side*(1.45+.06*sin(row)),.045,4-row*.65),Vector3(.9,1,.84),row*.12)
    for i in 10:
        place("PavingStone",Vector3(-3-i*.72,.046,-3.45+.13*sin(i)),Vector3.ONE,i*.21)
    for i in 8:
        var angle = i*2.399
        place("SunthreadCluster",Vector3(-5.8+cos(angle)*.8,0,.1+sin(angle)*.6),Vector3.ONE*.75,angle)
    ReefKit.batch_static(self,[],true)

func place(key: String, at: Vector3, size := Vector3.ONE, turn := 0.0) -> MeshInstance3D:
    assert(pieces.has(key),"Missing Dawnreef art piece: " + key)
    var instance = MeshInstance3D.new()
    instance.name = key
    instance.mesh = pieces[key]
    instance.position = at
    instance.scale = size
    instance.rotation.y = turn
    add_child(instance)
    return instance
