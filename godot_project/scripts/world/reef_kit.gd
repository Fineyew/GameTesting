class_name ReefKit
extends RefCounted
static var materials: Dictionary = {}

static func material(color: Color, glow := false) -> StandardMaterial3D:
    var key = str(color) + str(glow)
    if not materials.has(key):
        var mat = StandardMaterial3D.new()
        mat.albedo_color = color
        mat.roughness = 0.85
        if glow:
            mat.emission_enabled = true
            mat.emission = color
            mat.emission_energy_multiplier = 0.5
        materials[key] = mat
    return materials[key]

static func mesh(parent: Node3D, shape: Mesh, at: Vector3, color: Color, glow := false) -> MeshInstance3D:
    var node = MeshInstance3D.new()
    node.mesh = shape
    node.material_override = material(color, glow)
    node.position = at
    parent.add_child(node)
    return node

static func box(parent: Node3D, size: Vector3, at: Vector3, color: Color, collision := false) -> MeshInstance3D:
    var shape = BoxMesh.new()
    shape.size = size
    var node = mesh(parent, shape, at, color)
    if collision:
        var body = StaticBody3D.new()
        var collider = CollisionShape3D.new()
        var bounds = BoxShape3D.new()
        bounds.size = size
        collider.shape = bounds
        body.add_child(collider)
        node.add_child(body)
    return node

static func cylinder(parent: Node3D, radius: float, height: float, at: Vector3, color: Color, top := -1.0) -> MeshInstance3D:
    var shape = CylinderMesh.new()
    shape.bottom_radius = radius
    shape.top_radius = radius if top < 0 else top
    shape.height = height
    shape.radial_segments = 10
    shape.rings = 1
    return mesh(parent, shape, at, color)

static func sphere(parent: Node3D, radius: float, at: Vector3, color: Color, glow := false) -> MeshInstance3D:
    var shape = SphereMesh.new()
    shape.radius = radius
    shape.height = radius * 2
    shape.radial_segments = 12
    shape.rings = 6
    return mesh(parent, shape, at, color, glow)

static func label(parent: Node3D, words: String, at: Vector3) -> Label3D:
    var node = Label3D.new()
    node.text = words
    node.position = at
    node.font_size = 38
    node.pixel_size = .007
    node.outline_size = 8
    node.modulate = Color("f3ead5")
    node.billboard = BaseMaterial3D.BILLBOARD_ENABLED
    node.no_depth_test = false
    parent.add_child(node)
    return node

# Static geometry is merged by material. Collision children remain active on hidden source nodes.
static func batch_static(parent: Node3D, excluded: Array = []) -> void:
    var groups: Dictionary = {}
    for child in parent.get_children():
        if child is MeshInstance3D and not child in excluded:
            var key = child.material_override.get_instance_id()
            if not groups.has(key):
                groups[key] = {"surface": SurfaceTool.new(), "material": child.material_override}
                groups[key].surface.begin(Mesh.PRIMITIVE_TRIANGLES)
            groups[key].surface.append_from(child.mesh, 0, child.transform)
            child.visible = false
    for group in groups.values():
        var node = MeshInstance3D.new()
        node.mesh = group.surface.commit()
        node.material_override = group.material
        parent.add_child(node)
