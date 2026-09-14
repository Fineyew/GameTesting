"""M1.7 single-floor surface contract shared by live terrain and validation.

One-metre cells relative to integer bounds; millimetre SW/SE/NE/NW corners.
Queries and collision use the SW--NE diagonal, never bilinear interpolation.
This is geometry, not movement permission: capsule sweeps are a separate gate.
"""
import math
from types import MappingProxyType


from backend.app.core.terrain_schema import validate_surface


class TerrainSurface:
    def __init__(self, definition):
        self.bounds, cells = validate_surface(definition)
        self.width = self.bounds[2] - self.bounds[0]
        self.depth = self.bounds[3] - self.bounds[1]
        self.cells = MappingProxyType(cells)

    def corners(self, x, z):
        return self.cells.get((x, z), (0., 0., 0., 0.))

    def sample(self, x, z):
        if any(type(v) not in (int, float) or abs(v) > 4096 or not math.isfinite(v) for v in (x, z)):
            raise ValueError("nonfinite terrain query")
        b = self.bounds
        if not (b[0] <= x <= b[2] and b[1] <= z <= b[3]):
            raise ValueError("terrain query outside bounds")
        # Interior edges belong to their positive-axis cell; outer max to last cell.
        ix, iz = min(math.floor(x - b[0]), self.width - 1), min(math.floor(z - b[1]), self.depth - 1)
        u, v = x - b[0] - ix, z - b[1] - iz
        sw, se, ne, nw = self.corners(ix, iz)
        if v <= u:
            dx, dz, triangle = se - sw, ne - se, 0
        else:
            dx, dz, triangle = ne - nw, nw - sw, 1
        return {"height": sw + u * dx + v * dz,
                "slope_degrees": math.degrees(math.atan(math.hypot(dx, dz))),
                "cell": [ix, iz], "triangle": triangle}

    def triangles(self):
        """Clockwise Godot top faces; two-sided risers between discontinuous cells.

        Crossing edge profiles are split at their intersection to avoid bow-tie quads.
        No exterior skirt: world bounds, not invented cliff geometry, constrain entry.
        """
        faces = []
        for z in range(self.depth):
            for x in range(self.width):
                px, pz = self.bounds[0] + x, self.bounds[1] + z
                sw, se, ne, nw = self.corners(x, z)
                a, b, c, d = [px, sw, pz], [px+1, se, pz], [px+1, ne, pz+1], [px, nw, pz+1]
                faces.extend([[a, b, c], [a, c, d]])
                if x + 1 < self.width:
                    other = self.corners(x+1, z)
                    faces.extend(_riser(b, c, [px+1, other[0], pz], [px+1, other[3], pz+1]))
                if z + 1 < self.depth:
                    other = self.corners(x, z+1)
                    faces.extend(_riser(d, c, [px, other[0], pz+1], [px+1, other[1], pz+1]))
        return faces


def _riser(a, b, c, d):
    start, end = a[1]-c[1], b[1]-d[1]
    if start * end < 0:
        t = start / (start - end)
        mid = [a[i] + t*(b[i]-a[i]) for i in range(3)]
        return _riser(a, mid, c, mid) + _riser(mid, b, mid, d)
    result = []
    # Skip the degenerate triangle when one endpoint joins continuously.
    if start != 0:
        result.extend([[a, c, b], [b, c, a]])
    if end != 0:
        result.extend([[b, c, d], [d, c, b]])
    return result
