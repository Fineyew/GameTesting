class_name TerrainSurface
extends RefCounted
## M1.7 geometry only. Live movement/protocol remain planar until sweep validation.
var _bounds: Array = []
var _cells: Dictionary = {}
var _width: int
var _depth: int

static func _integer(value: Variant, limit: int) -> bool:
    # JSON numbers are floats in Godot, but booleans must never become heights.
    return (value is int or value is float) and is_finite(float(value)) and absf(float(value)) <= limit and float(value) == floorf(float(value))

func configure(definition: Variant) -> String:
    # Invalid reconfiguration invalidates the old surface instead of retaining it.
    _bounds = []
    _cells = {}
    if not definition is Dictionary or definition.size() != 2 or not definition.has_all(["bounds", "cells"]):
        return "terrain requires only bounds and cells"
    var bounds = definition.bounds
    if not bounds is Array or bounds.size() != 4:
        return "terrain bounds must be four bounded integers"
    for value in bounds:
        if not _integer(value, 4096):
            return "terrain bounds must be four bounded integers"
    var width = int(bounds[2] - bounds[0])
    var depth = int(bounds[3] - bounds[1])
    if width < 1 or width > 128 or depth < 1 or depth > 128:
        return "terrain extent must be 1..128 metres per axis"
    if not definition.cells is Dictionary or definition.cells.size() > width * depth:
        return "invalid terrain cell map"
    var pattern = RegEx.new()
    pattern.compile("^(0|[1-9][0-9]*):(0|[1-9][0-9]*)$")
    for key in definition.cells:
        if not key is String or pattern.search(key) == null or pattern.search(key).get_string() != key:
            return "noncanonical terrain cell key"
        var parts = key.split(":")
        # Bound string length before converting to avoid integer overflow.
        if parts[0].length() > 3 or parts[1].length() > 3 or int(parts[0]) >= width or int(parts[1]) >= depth:
            return "terrain cell outside bounds"
        var heights = definition.cells[key]
        if not heights is Array or heights.size() != 4:
            return "invalid terrain corners"
        for value in heights:
            if not _integer(value, 8000):
                return "invalid terrain corners"
    _bounds = bounds.duplicate()
    _cells = definition.cells.duplicate(true)
    _width = width
    _depth = depth
    return ""

func corners(x: int, z: int) -> Array:
    var mm = _cells.get("%d:%d" % [x,z], [0,0,0,0])
    return [mm[0]/1000.0, mm[1]/1000.0, mm[2]/1000.0, mm[3]/1000.0]

func sample(x: float, z: float) -> Dictionary:
    if _bounds.is_empty() or not is_finite(x) or not is_finite(z):
        return {}
    if x < _bounds[0] or x > _bounds[2] or z < _bounds[1] or z > _bounds[3]:
        return {}
    var ix = mini(floori(x-_bounds[0]), _width-1)
    var iz = mini(floori(z-_bounds[1]), _depth-1)
    var u = x-_bounds[0]-ix
    var v = z-_bounds[1]-iz
    var h = corners(ix, iz)
    var dx: float
    var dz: float
    var triangle: int
    if v <= u:
        dx = h[1]-h[0]
        dz = h[2]-h[1]
        triangle = 0
    else:
        dx = h[2]-h[3]
        dz = h[3]-h[0]
        triangle = 1
    return {"height":h[0]+u*dx+v*dz, "slope_degrees":rad_to_deg(atan(sqrt(dx*dx+dz*dz))), "cell":[ix,iz], "triangle":triangle}

func triangles() -> Array:
    var faces: Array = []
    if _bounds.is_empty():
        return faces
    for z in range(_depth):
        for x in range(_width):
            var px = _bounds[0]+x
            var pz = _bounds[1]+z
            var h = corners(x,z)
            var a = [px,h[0],pz]
            var b = [px+1,h[1],pz]
            var c = [px+1,h[2],pz+1]
            var d = [px,h[3],pz+1]
            faces.append_array([[a,b,c],[a,c,d]])
            if x+1 < _width:
                var other = corners(x+1,z)
                faces.append_array(_riser(b,c,[px+1,other[0],pz],[px+1,other[3],pz+1]))
            if z+1 < _depth:
                var other = corners(x,z+1)
                faces.append_array(_riser(d,c,[px,other[0],pz+1],[px+1,other[1],pz+1]))
    return faces

static func _riser(a: Array, b: Array, c: Array, d: Array) -> Array:
    var start: float = a[1]-c[1]
    var finish: float = b[1]-d[1]
    if start*finish < 0:
        var t = start/(start-finish)
        var mid = []
        for i in range(3):
            mid.append(a[i]+t*(b[i]-a[i]))
        return _riser(a,mid,c,mid)+_riser(mid,b,mid,d)
    var result: Array = []
    if start != 0:
        result.append_array([[a,c,b],[b,c,a]])
    if finish != 0:
        result.append_array([[b,c,d],[d,c,b]])
    return result

func collision_shape() -> ConcavePolygonShape3D:
    var vertices = PackedVector3Array()
    for face in triangles():
        for p in face:
            vertices.append(Vector3(p[0],p[1],p[2]))
    var shape = ConcavePolygonShape3D.new()
    shape.set_faces(vertices)
    return shape
