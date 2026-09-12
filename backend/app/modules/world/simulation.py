"""Fixed-step planar authority, sharing dimensions with the client collision scene."""
import math
from backend.app.modules.world.terrain import TerrainSurface
from backend.app.modules.world.traversal import move


def step(position, velocity, axis, dt, geometry, surface=None):
    if not 0 < dt <= .1:
        raise ValueError("invalid world tick")
    length = math.hypot(*axis)
    axis = [v / max(1.0, length) for v in axis]
    acceleration = geometry.get("acceleration", 16) if length > 0 else geometry.get("deceleration", 24)
    speed, radius = geometry.get("speed", 4.8), geometry.get("radius", .35)
    pos, vel = list(position), list(velocity)
    bounds = geometry["bounds"]
    if "terrain" in geometry:
        surface = surface or TerrainSurface(geometry["terrain"])
        for dimension in range(2):
            difference = axis[dimension]*speed-vel[dimension]
            vel[dimension] += max(-acceleration*dt,min(acceleration*dt,difference))
        pos, stopped = move(surface,pos,[v*dt for v in vel],geometry["blockers"])
        return pos, [0 if stopped[i] else vel[i] for i in range(2)]
    for dimension in range(2):
        difference = axis[dimension] * speed - vel[dimension]
        vel[dimension] += max(-acceleration * dt, min(acceleration * dt, difference))
        candidate = list(pos)
        candidate[dimension] = max(bounds[dimension] + radius, min(bounds[dimension + 2] - radius, pos[dimension] + vel[dimension] * dt))
        if any(b[0]-radius < candidate[0] < b[2]+radius and b[1]-radius < candidate[1] < b[3]+radius for b in geometry["blockers"]):
            vel[dimension] = 0
        else:
            pos = candidate
    return pos, vel
