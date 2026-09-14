"""Conservative capsule clearance for the first single-floor route.

The swept square encloses the .35m capsule footprint: never under-clear a corner.
This deliberately trades some corner clearance for deterministic mobile/server parity.
No jumping, falling, stacked floors or client-declared altitude.
"""
import math


def clear(surface, start, end, blockers, radius=.35):
    box = [min(start[0],end[0])-radius,min(start[1],end[1])-radius,
           max(start[0],end[0])+radius,max(start[1],end[1])+radius]
    bounds = surface.bounds
    if box[0] < bounds[0]-1e-8 or box[1] < bounds[1]-1e-8 or box[2] > bounds[2]+1e-8 or box[3] > bounds[3]+1e-8:
        return False
    if any(box[0] < b[2]-1e-8 and box[2] > b[0]+1e-8 and box[1] < b[3]-1e-8 and box[3] > b[1]+1e-8 for b in blockers):
        return False
    lo_x = max(0,math.floor(box[0]-bounds[0]+1e-8))
    lo_z = max(0,math.floor(box[1]-bounds[1]+1e-8))
    hi_x = min(surface.width-1,math.floor(box[2]-bounds[0]-1e-8))
    hi_z = min(surface.depth-1,math.floor(box[3]-bounds[1]-1e-8))
    for z in range(lo_z,hi_z+1):
        for x in range(lo_x,hi_x+1):
            sw,se,ne,nw = surface.corners(x,z)
            # Check both faces of touched cells: conservative at a diagonal seam.
            if max(math.hypot(se-sw,ne-se), math.hypot(ne-nw,nw-sw)) > math.tan(math.radians(42))+1e-8:
                return False
            if x < hi_x:
                h = surface.corners(x+1,z)
                if max(abs(se-h[0]),abs(ne-h[3])) > .30+1e-8:
                    return False
            if z < hi_z:
                h = surface.corners(x,z+1)
                if max(abs(nw-h[0]),abs(ne-h[1])) > .30+1e-8:
                    return False
    return True


def move(surface, position, displacement, blockers):
    if len(position) != 2 or len(displacement) != 2 or any(type(v) not in (int,float) or abs(v)>4096 or not math.isfinite(v) for v in [*position,*displacement]):
        raise ValueError("invalid traversal input")
    distance = math.hypot(*displacement)
    if distance > 2:
        raise ValueError("traversal exceeds bounded tick")
    pos = list(position)
    stopped = [False,False]
    count = max(1,math.ceil(distance/.1))
    for _ in range(count):
        for axis in range(2):
            candidate = list(pos)
            candidate[axis] += displacement[axis]/count
            if clear(surface,pos,candidate,blockers):
                pos = candidate
            else:
                stopped[axis] = True
    return pos, stopped
