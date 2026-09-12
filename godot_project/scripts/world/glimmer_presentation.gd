class_name GlimmerPresentation
extends Node3D
## One bounded, non-authoritative spell presentation; other spells retain their hooks.
signal impact
const DURATION = 1.15
var elapsed := 0.0
var origin: Vector3
var target: Vector3
var spark: MeshInstance3D
var trail: MeshInstance3D
var lens: MeshInstance3D
var fragments: Array[MeshInstance3D] = []
var struck := false

func begin(from: Vector3, to: Vector3) -> void:
    origin = from
    target = to
    spark = ReefKit.sphere(self,.09,origin,Color("ffe7a4"),true)
    trail = MeshInstance3D.new()
    trail.material_override = ReefKit.material(Color("d5b674"),true)
    add_child(trail)
    var ring = TorusMesh.new()
    ring.inner_radius = .60
    ring.outer_radius = .65
    ring.rings = 24
    ring.ring_segments = 6
    lens = ReefKit.mesh(self,ring,origin,Color("e8bd73"),true)
    lens.rotation.x = PI/2
    for i in 8:
        var shard = ReefKit.box(self,Vector3(.045,.15,.045),target,Color("ffdda0"))
        shard.material_override = ReefKit.material(Color("ffdda0"),true)
        shard.visible = false
        fragments.append(shard)

func _process(delta: float) -> void:
    elapsed += delta
    var flight = clampf((elapsed-.25)/.4,0,1)
    var fade = clampf((elapsed-.7)/.45,0,1)
    spark.position = path(flight)
    spark.scale = Vector3.ONE*(1+sin(minf(elapsed,.25)/.25*PI)*1.2)*(1-fade)
    lens.position = target if struck else origin
    lens.scale = Vector3.ONE*(.4+elapsed*1.4)*(1-fade)
    lens.rotation.z = elapsed*1.2
    if flight > 0 and fade < 1:
        var surface = SurfaceTool.new()
        surface.begin(Mesh.PRIMITIVE_TRIANGLES)
        for i in 12:
            var t0 = maxf(0,flight-.45)+minf(flight,.45)*i/12
            var t1 = maxf(0,flight-.45)+minf(flight,.45)*(i+1)/12
            var a = path(t0)
            var b = path(t1)
            var width = Vector3.UP*.035*(i+1)/12*(1-fade)
            for v in [a-width,a+width,b+width,a-width,b+width,b-width,
                    b+width,a+width,a-width,b-width,b+width,a-width]:
                surface.add_vertex(v)
        surface.generate_normals()
        trail.mesh = surface.commit()
    if flight >= 1 and not struck:
        struck = true
        impact.emit()
    if struck:
        for i in fragments.size():
            var angle = i*TAU/fragments.size()
            var shard = fragments[i]
            shard.visible = true
            shard.position = target + Vector3(cos(angle),sin(angle),sin(angle*.5)*.3)*(.1+fade*1.2)
            shard.rotation = Vector3(angle,0,elapsed*3)
            shard.scale = Vector3.ONE*(1-fade)
    if elapsed >= DURATION:
        queue_free()

func path(t: float) -> Vector3:
    return origin.lerp(target,t) + Vector3.UP*sin(t*PI)*.38
