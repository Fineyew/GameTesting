class_name WayfarerAvatar
extends Node3D
var walking := false
var elapsed := 0.0
var torso: Node3D
var legs: Array[MeshInstance3D] = []

func build(appearance: Dictionary) -> void:
    var robe = Color({"teal": "287d7e", "coral": "c66a61", "indigo": "665997"}.get(appearance.get("robe", "teal"), "287d7e"))
    var skin = Color({"warm": "c38d65", "deep": "795443", "pale": "e3baa0"}.get(appearance.get("skin", "warm"), "c38d65"))
    torso = Node3D.new()
    add_child(torso)
    ReefKit.cylinder(torso, .38, .86, Vector3(0,.9,0), robe, .24)
    ReefKit.cylinder(torso, .28, .12, Vector3(0,1.29,0), Color("d2ae68"))
    ReefKit.sphere(torso, .23, Vector3(0,1.59,0), skin)
    var hair = ReefKit.sphere(torso, .24, Vector3(0,1.72,.04), Color("3b3546"))
    hair.scale = Vector3(1,.62,1)
    for x in [-.14,.14]:
        legs.append(ReefKit.box(self, Vector3(.18,.45,.23), Vector3(x,.23,0), Color("293541")))
        ReefKit.cylinder(torso, .095, .52, Vector3(x*2.2,1.02,0), robe)
    ReefKit.cylinder(torso, .035, 1.55, Vector3(-.44,.98,-.1), Color("735943"))
    ReefKit.sphere(torso, .1, Vector3(-.44,1.8,-.1), Color("f1c66e"), true)

func _process(delta: float) -> void:
    elapsed += delta
    if torso:
        torso.position.y = sin(elapsed * (10 if walking else 2)) * (.022 if walking else .008)
    for index in legs.size():
        legs[index].rotation.x = sin(elapsed*10 + index*PI) * .45 if walking else 0.0
