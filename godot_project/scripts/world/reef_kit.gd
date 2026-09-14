class_name ReefKit
extends RefCounted
static var materials: Dictionary = {}
static var ground_materials: Dictionary = {}
static var contact_material: ShaderMaterial

static func camera_canopy(parent: Node3D, at: Vector3, radius: float) -> void:
    # Layer 2 obstructs cameras only. Player/world movement remains on catalog layer 1.
    var body = StaticBody3D.new()
    body.collision_layer = 2
    body.collision_mask = 0
    var collider = CollisionShape3D.new()
    var shape = SphereShape3D.new()
    shape.radius = radius
    collider.shape = shape
    body.add_child(collider)
    body.position = at
    parent.add_child(body)

static func ground(color: Color) -> ShaderMaterial:
    var key = color.to_html()
    if not ground_materials.has(key):
        var mat = ShaderMaterial.new()
        mat.shader = preload("res://assets/dawnreef/ground.gdshader")
        mat.set_shader_parameter("ground_color",color)
        ground_materials[key] = mat
    return ground_materials[key]

static func contact_shadow(parent: Node3D, at: Vector3, size: Vector2) -> void:
    if contact_material == null:
        contact_material = ShaderMaterial.new()
        contact_material.shader = preload("res://assets/dawnreef/contact_shadow.gdshader")
    var shape = PlaneMesh.new()
    shape.size = size
    var node = MeshInstance3D.new()
    node.mesh = shape
    node.material_override = contact_material
    node.position = at
    node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    parent.add_child(node)

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
    node.visibility_range_end = 24
    parent.add_child(node)
    return node

# Static geometry is merged by material. Collision children remain active on hidden source nodes.
static func batch_static(parent: Node3D, excluded: Array = [], recursive := false) -> void:
    var groups: Dictionary = {}
    var candidates = parent.find_children("*","MeshInstance3D",true,false) if recursive else parent.get_children()
    for child in candidates:
        if child is MeshInstance3D and child.visible and not child in excluded:
            for surface in child.mesh.get_surface_count():
                var active_material = child.get_active_material(surface)
                if active_material == null:
                    continue
                var key = str(active_material.get_instance_id()) + ":" + str(child.cast_shadow)
                if not groups.has(key):
                    groups[key] = {"surface": SurfaceTool.new(), "material": active_material, "shadow":child.cast_shadow}
                    groups[key].surface.begin(Mesh.PRIMITIVE_TRIANGLES)
                var relative = parent.global_transform.affine_inverse() * child.global_transform
                groups[key].surface.append_from(child.mesh,surface,relative)
            child.visible = false
    for group in groups.values():
        var node = MeshInstance3D.new()
        node.mesh = group.surface.commit()
        node.material_override = group.material
        node.cast_shadow = group.shadow
        parent.add_child(node)
