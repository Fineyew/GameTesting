"""Authoring checks for the currently executable world contract.

Keep this in content: validation must not import the world simulation internals.
Elevation uses the core schema shared with simulation; runtime negotiates protocol2.
"""
import math
from backend.app.core.terrain_schema import validate_surface


def geometry_errors(world):
    errors = []
    required = {"bounds", "spawn", "blockers", "interactions"}
    allowed = required | {"speed", "acceleration", "deceleration", "radius", "terrain", "geometry_revision"}
    if not isinstance(world, dict):
        return ["world must be an object"]
    if not required <= world.keys() or world.keys() - allowed:
        errors.append("world requires bounds/spawn/blockers/interactions and only supported fields")

    def number(value, minimum, maximum):
        return type(value) in (int, float) and minimum <= value <= maximum and math.isfinite(value) and abs(value*1000-round(value*1000)) <= 1e-8

    def coordinates(value, size):
        return isinstance(value, list) and len(value) == size and all(number(v, -512, 512) for v in value)

    bounds = world.get("bounds")
    if not coordinates(bounds, 4) or bounds[2] - bounds[0] < 2 or bounds[3] - bounds[1] < 2:
        errors.append("world bounds require four finite coordinates and at least two metres on each axis")
        bounds = None
    if "terrain" in world:
        try:
            terrain_bounds, cells = validate_surface(world["terrain"])
            if bounds is None or list(terrain_bounds) != bounds or world.get("geometry_revision") != 2 or type(world.get("geometry_revision")) is not int:
                errors.append("world terrain requires matching bounds and geometry_revision2")
            # Keep entry and story approaches flat in this first activation.
            for at in [world.get("spawn"), *world.get("interactions",{}).values()] if isinstance(world.get("interactions"),dict) else []:
                if coordinates(at,2):
                    for (x,z), heights in cells.items():
                        if any(heights) and terrain_bounds[0]+x-4 <= at[0] <= terrain_bounds[0]+x+5 and terrain_bounds[1]+z-4 <= at[1] <= terrain_bounds[1]+z+5:
                            errors.append("world elevation must preserve flat entry and interaction approaches")
        except (ValueError,TypeError):
            errors.append("world terrain descriptor is invalid")
    # Godot's existing capsule/clamp are .35; accepting a different server radius
    # here would silently create different collision rules across the two runtimes.
    radius = world.get("radius", .35)
    if type(radius) not in (int, float) or radius != .35:
        errors.append("world radius must match the current client capsule (0.35)")
    for key, default, maximum in (("speed", 4.8, 12), ("acceleration", 16, 64), ("deceleration", 24, 64)):
        if not number(world.get(key, default), .1, maximum):
            errors.append(f"world {key} must be finite and between 0.1 and {maximum}")

    blockers = world.get("blockers")
    valid_blockers = []
    if not isinstance(blockers, list) or len(blockers) > 128:
        errors.append("world blockers must be a list of at most 128 rectangles")
    else:
        for index, rectangle in enumerate(blockers):
            if not coordinates(rectangle, 4) or rectangle[0] >= rectangle[2] or rectangle[1] >= rectangle[3]:
                errors.append(f"world blocker {index} requires an ordered finite rectangle")
            elif bounds and not (bounds[0] <= rectangle[0] < rectangle[2] <= bounds[2] and bounds[1] <= rectangle[1] < rectangle[3] <= bounds[3]):
                errors.append(f"world blocker {index} must be within bounds")
            else:
                valid_blockers.append(rectangle)

    spawn = world.get("spawn")
    if not coordinates(spawn, 2):
        errors.append("world spawn requires two finite coordinates")
    elif bounds:
        if not (bounds[0] + .35 <= spawn[0] <= bounds[2] - .35 and bounds[1] + .35 <= spawn[1] <= bounds[3] - .35):
            errors.append("world spawn must fit inside bounds with capsule clearance")
        if any(b[0] - .35 < spawn[0] < b[2] + .35 and b[1] - .35 < spawn[1] < b[3] + .35 for b in valid_blockers):
            errors.append("world spawn overlaps a blocker or its capsule clearance")

    interactions = world.get("interactions")
    if not isinstance(interactions, dict) or len(interactions) > 128:
        errors.append("world interactions must be an object of at most 128 landmarks")
    else:
        for key, at in interactions.items():
            if not isinstance(key, str) or not 1 <= len(key) <= 64 or not coordinates(at, 2):
                errors.append("world interaction requires a nonempty key and two finite coordinates")
            elif bounds and not (bounds[0] <= at[0] <= bounds[2] and bounds[1] <= at[1] <= bounds[3]):
                errors.append(f"world interaction {key} must be within bounds")
    return errors
