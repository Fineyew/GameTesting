class_name TerrainTraversal
extends RefCounted
## Conservative swept square enclosing the existing 0.35m capsule footprint.
static func clear(surface: TerrainSurface, start: Vector2, finish: Vector2, blockers: Array) -> bool:
    var box = [minf(start.x,finish.x)-.35,minf(start.y,finish.y)-.35,maxf(start.x,finish.x)+.35,maxf(start.y,finish.y)+.35]
    var bounds = surface._bounds
    if box[0]<bounds[0]-.00000001 or box[1]<bounds[1]-.00000001 or box[2]>bounds[2]+.00000001 or box[3]>bounds[3]+.00000001:
        return false
    for b in blockers:
        if box[0]<b[2]-.00000001 and box[2]>b[0]+.00000001 and box[1]<b[3]-.00000001 and box[3]>b[1]+.00000001:
            return false
    var lo_x = maxi(0,floori(box[0]-bounds[0]+.00000001))
    var lo_z = maxi(0,floori(box[1]-bounds[1]+.00000001))
    var hi_x = mini(surface._width-1,floori(box[2]-bounds[0]-.00000001))
    var hi_z = mini(surface._depth-1,floori(box[3]-bounds[1]-.00000001))
    for z in range(lo_z,hi_z+1):
        for x in range(lo_x,hi_x+1):
            var h = surface.corners(x,z)
            var a = sqrt(pow(h[1]-h[0],2)+pow(h[2]-h[1],2))
            var b = sqrt(pow(h[2]-h[3],2)+pow(h[3]-h[0],2))
            if maxf(a,b)>tan(deg_to_rad(42))+.00000001:
                return false
            if x<hi_x:
                var other = surface.corners(x+1,z)
                if maxf(absf(h[1]-other[0]),absf(h[2]-other[3]))>.30+.00000001:
                    return false
            if z<hi_z:
                var other = surface.corners(x,z+1)
                if maxf(absf(h[3]-other[0]),absf(h[2]-other[1]))>.30+.00000001:
                    return false
    return true

static func move(surface: TerrainSurface, position: Vector2, displacement: Vector2, blockers: Array) -> Dictionary:
    if not position.is_finite() or not displacement.is_finite() or displacement.length()>2:
        return {"position":position,"stopped":[true,true]}
    var pos = position
    var stopped = [false,false]
    var count = maxi(1,ceili(displacement.length()/.1))
    for _i in range(count):
        for axis in range(2):
            var candidate = pos
            candidate[axis] += displacement[axis]/count
            if clear(surface,pos,candidate,blockers):
                pos = candidate
            else:
                stopped[axis] = true
    return {"position":pos,"stopped":stopped}
