"""Original Dawnreef benchmark art. Run with Blender 4.5.3 --background --python.

Godot coordinates are used in the authoring recipes: metres, Y up, forward -Z.
The .blend is editable source; exported GLBs are the engine inputs. No Blender
installation is required to run the game or its ordinary CI/export pipeline.
All geometry/palette/rig/motion here is authored for Veilbound Tides; no asset pack.
"""
from pathlib import Path
import math
import random
import json
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'godot_project/assets/dawnreef'
SOURCE = ROOT / 'art_sources/dawnreef'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)
RNG = random.Random(4096)
PALETTE = {
    'stone': 'c6bca0', 'light_stone': 'e1d5b7', 'mortar': '7b897e',
    'wood': '705342', 'wood_light': 'ae8660', 'teal': '327778',
    'teal_dark': '244d59', 'teal_light': '6ba49a', 'copper': 'c9955b',
    'gold': 'e4be79', 'paper': 'ebe1c1', 'leaf': '407f65',
    'leaf_light': '86ac76', 'leaf_dark': '305f54', 'coral': 'b76e5d',
    'luminous': 'ffdfa0', 'ink': '263744', 'berry': '7c5266',
}


def xyz(p):
    return Vector((p[0], -p[2], p[1]))


def rgb(color):
    color = PALETTE.get(color, color)
    values = [int(color[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values)


def material(name, emission=False):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes = mat.node_tree.nodes
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .86
    shader.inputs['Metallic'].default_value = 0
    color = nodes.new('ShaderNodeVertexColor')
    color.layer_name = 'Paint'
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    if emission:
        mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Emission Color'])
        shader.inputs['Emission Strength'].default_value = .8
    return mat


def paint(obj, color, mat=None, shade=True):
    obj.data.materials.clear()
    obj.data.materials.append(mat or PAINT)
    attr = obj.data.color_attributes.new(name='Paint', type='FLOAT_COLOR', domain='CORNER')
    base = rgb(color)
    heights = [v.co.z for v in obj.data.vertices]
    low, high = min(heights), max(heights)
    for poly in obj.data.polygons:
        # Authored vertex tint supplies soft material variation, not runtime AO.
        light = .92 + .08 * max(poly.normal.z, 0) if shade else 1
        for idx in poly.loop_indices:
            v = obj.data.vertices[obj.data.loops[idx].vertex_index]
            factor = light * (.88 + .12*(v.co.z-low)/max(.001, high-low)) if shade else 1
            attr.data[idx].color = (*[c*factor for c in base], 1)
    obj.data.color_attributes.active_color = attr
    return obj


def apply(obj, modifier):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def box(name, at, size, color, bevel=.04, rotation=0, mat=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=xyz(at))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new('Soft crafted edges', 'BEVEL')
        mod.width = min(bevel, min(size)*.22)
        mod.segments = 2
        apply(obj, mod)
    obj.rotation_euler.z = rotation
    return paint(obj, color, mat)


def mesh(name, vertices, faces, color, mat=None, smooth=False):
    # Back faces need distinct vertices: duplicate face indices are invalid in
    # Blender and are removed during glTF validation, even with opposite winding.
    vertices = list(vertices)
    unique_faces, seen = [], set()
    for face in faces:
        key = tuple(sorted(face))
        if key in seen:
            start = len(vertices)
            vertices.extend(vertices[i] for i in face)
            face = tuple(range(start, len(vertices)))
        seen.add(key)
        unique_faces.append(face)
    data = bpy.data.meshes.new(name)
    data.from_pydata([xyz(v) for v in vertices], [], unique_faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    for poly in data.polygons:
        poly.use_smooth = smooth
    return paint(obj, color, mat)


def orb(name, at, size, color, mat=None, segments=16, rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=xyz(at))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return paint(obj, color, mat)


def beam(name, a, b, radius, color, end_radius=None, vertices=10, mat=None):
    a, b = xyz(a), xyz(b)
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius,
        radius2=radius if end_radius is None else end_radius, depth=(b-a).length,
        location=(a+b)*.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    return paint(obj, color, mat)


def ring(name, at, radius, thickness, color, arc=math.tau, tilt=0, mat=None, segments=40):
    verts, faces = [], []
    steps = max(4, round(segments*arc/math.tau))
    for i in range(steps+1):
        angle = i*arc/steps
        for j in range(6):
            q = j*math.tau/6
            x = (radius+thickness*math.cos(q))*math.cos(angle)
            z = (radius+thickness*math.cos(q))*math.sin(angle)
            y = thickness*math.sin(q)
            yy, zz = y*math.cos(tilt)-z*math.sin(tilt), y*math.sin(tilt)+z*math.cos(tilt)
            verts.append((at[0]+x, at[1]+yy, at[2]+zz))
    for i in range(steps):
        for j in range(6):
            a=i*6+j; b=i*6+(j+1)%6
            faces.append((a,b,b+6,a+6))
    return mesh(name,verts,faces,color,mat,smooth=True)


def lathe(name, at, profile, color, sides=16, mat=None):
    verts=[]; faces=[]
    for radius,height in profile:
        for i in range(sides):
            a=i*math.tau/sides
            verts.append((at[0]+radius*math.cos(a),at[1]+height,at[2]+radius*math.sin(a)))
    for k in range(len(profile)-1):
        for i in range(sides):
            a=k*sides+i; b=k*sides+(i+1)%sides
            faces.append((a,a+sides,b+sides,b))
    faces.extend([tuple(range(sides)),tuple((len(profile)-1)*sides+i for i in reversed(range(sides)))])
    return mesh(name,verts,faces,color,mat,smooth=True)


def leaf(name, a, b, width, color):
    a,b=Vector(a),Vector(b)
    along=b-a
    across=along.cross(Vector((0,0,1))).normalized()*width
    if across.length < .001: across=Vector((width,0,0))
    mid=a+along*.48
    ridge=mid+Vector((0,0,-width*.18))
    vs=[a,mid+across,b,mid-across,ridge]
    fs=[(0,1,4),(1,2,4),(2,3,4),(3,0,4)]
    fs += [tuple(reversed(f)) for f in fs]
    return mesh(name,[tuple(v) for v in vs],fs,color)


def join_objects(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if len(objects) > 1:
        bpy.ops.object.join()
    obj=bpy.context.object
    obj.name=name
    bpy.context.scene.cursor.location=(0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    # A joined mesh inherits its first object's rotation. Bake that orientation so
    # source bounds, exported bounds and scene placement use the same upright axes.
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    return obj


def export(objects, stem, save_source=True):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if save_source:
        bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(stem+'.blend')), compress=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT/(stem+'.glb')),export_format='GLB',
        use_selection=True,export_animations=True,export_force_sampling=True,
        export_materials='EXPORT',export_cameras=False,export_lights=False,
        export_extras=True)


def asset(name, recipe):
    before=set(bpy.data.objects)
    recipe()
    objects=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    return join_objects(objects,name)


def well():
    # A shallow inscribed floor lens keeps the existing flat walkable footprint.
    lathe('Lens stone', (0,0,0), [(1.85,.018),(1.85,.065),(1.66,.075),(1.6,.08)], 'stone', 40)
    lathe('Reflective basin',(0,0,0),[(1.5,.08),(1.5,.086)],'teal_dark',40)
    for rad in [1.58,1.33,.81]: ring('Inlaid brass',(0,.09,0),rad,.022,'copper')
    for i in range(12):
        a=i*math.tau/12
        box('Radial inscription',(math.cos(a)*1.12,.095,math.sin(a)*1.12),(.28,.015,.045),'gold',.004,-a)
    for i in range(6):
        a=i*math.tau/6
        beam('Floating lens claw',(math.cos(a)*.44,1.45,math.sin(a)*.44),(math.cos(a)*.19,1.14,math.sin(a)*.19),.028,'copper',.012)
    ring('Suspended lens cage',(0,1.52,0),.62,.033,'gold',tilt=.42)
    ring('Suspended cross ring',(0,1.52,0),.51,.025,'copper',tilt=1.95)
    lathe('Lantern crown',(0,1.72,0),[(.12,0),(.31,.12),(.12,.28),(.02,.54)],'gold',12)
    for i in [-1,1]:
        # Floating sail-shaped stone vanes, deliberately above player head height.
        faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
        if i<0: faces=[tuple(reversed(face)) for face in faces]
        mesh('Skyward sail',[(i*.85,2.45,-.35),(i*1.85,2.7,-.16),(i*1.4,3.25,0),(i*.58,3.42,.06),
              (i*.85,2.45,-.18),(i*1.85,2.7,.01),(i*1.4,3.25,.17),(i*.58,3.42,.23)],
             faces,'light_stone')
    ring('Upper suspension',(0,2.65,0),1.28,.022,'copper',arc=math.pi*1.5)


def cart():
    box('Frame',(0,.63,0),(2.35,.2,1.28),'wood')
    for i in range(8): box('Slatted body',(-1.06+i*.3,.99,.56),(.245,.65,.06),'wood_light',.015)
    for z in [-.54,.58]:
        for y in [.72,1.3]: box('Rim',(0,y,z),(2.5,.085,.11),'wood',.025)
    for x in [-1.2,1.2]: box('End panel',(x,1.04,0),(.11,.63,1.3),'wood_light')
    for x in [-1.18,1.18]:
        for z in [-.64,.64]:
            beam('Canopy post',(x,.7,z),(x,2.75,z),.038,'wood')
    for x in [-1.28,1.28]:
        for z in [-.34,.34]:
            wheel=ring('Cartwheel',(0,0,0),.34,.06,'wood',tilt=math.pi/2)
            wheel.location=xyz((x,.39,z))
            wheel.rotation_euler.z=math.pi/2
            for i in range(8):
                a=i*math.tau/8
                beam('Wheel spoke',(x,.39,z),(x,.39+math.sin(a)*.29,z+math.cos(a)*.29),.022,'copper')
    # Six curved woven canopy strips with a scalloped edge.
    for strip in range(6):
        verts=[]; faces=[]
        for row in range(9):
            z=-.86+row*.215
            y=2.74+.34*math.sin(row*math.pi/8)
            verts.extend([(strip*.46-1.38,y,z),((strip+1)*.46-1.38,y,z)])
        for row in range(8): faces.extend([(row*2,row*2+1,row*2+3,row*2+2),(row*2+2,row*2+3,row*2+1,row*2)])
        mesh('Woven canopy',verts,faces,'teal' if strip%2==0 else 'paper')
        x=-1.15+strip*.46
        mesh('Canopy scallop',[(x-.23,2.74,.86),(x+.23,2.74,.86),(x+.16,2.48,.89),(x,2.43,.9),(x-.16,2.48,.89)],
             [(0,1,2,3,4),(4,3,2,1,0)],'teal' if strip%2==0 else 'paper')
    for i in range(5):
        x=-.87+i*.36
        lathe('Supply flask',(x,1.34,-.05),[(.1,0),(.13,.06),(.13,.27),(.055,.34),(.055,.42)],['teal_light','coral','gold'][i%3],10)
        box('Cork',(x,1.78,-.05),(.09,.06,.09),'wood_light',.015)
    for i in range(3): box('Linen bundle',(.56,1.43+i*.11,.33),(.57,.09,.28),'paper',.025,rotation=.08*i)
    for i in range(2): box('Folio stack',(-.74,1.4+i*.08,.27),(.44,.07,.42),'berry' if i else 'teal_dark',.015,rotation=.1)


def planter():
    lathe('Planter',(0,0,0),[(.25,0),(.34,.08),(.46,.57),(.48,.64),(.4,.7)],'coral',14)
    ring('Planter band',(0,.61,0),.45,.025,'gold',segments=28)
    for i in range(13):
        a=i*2.399; reach=.28+(i%3)*.08
        leaf('Fan leaf',(0,.67,0),(math.cos(a)*reach,1.0+(i%4)*.13,math.sin(a)*reach),.12,
             'leaf_light' if i%3==0 else 'leaf')


def lantern():
    box('Post foot',(0,.15,0),(.42,.3,.42),'stone',.055)
    beam('Lantern post',(0,.3,0),(.12,2.55,0),.07,'wood',.04)
    beam('Crooked arm',(.12,2.55,0),(.66,2.7,0),.05,'wood',.035)
    beam('Lantern chain',(.64,2.68,0),(.64,2.4,0),.015,'copper')
    lathe('Lantern glass',(.64,1.94,0),[(.1,0),(.2,.08),(.2,.3),(.1,.42)],'luminous',8,GLOW)
    for h in [2.01,2.29]: ring('Copper rim',(.64,h,0),.205,.022,'copper',segments=16)
    for i in range(4):
        a=i*math.pi/2
        beam('Frame',(.64+.19*math.cos(a),2.02,.19*math.sin(a)),(.64+.19*math.cos(a),2.3,.19*math.sin(a)),.018,'copper')
    lathe('Lantern roof',(.64,2.3,0),[(.24,0),(.08,.13),(.02,.2)],'teal_dark',8)


def house():
    # Unit footprint is 8 x 6; world collision stays in the catalog's exact rectangles.
    box('Warm plaster',(0,1.55,0),(8,3.1,6),'light_stone',.09)
    for y in [.18,.48]: box('Foundation',(0,y,0),(8.1,.24,6.1),'stone',.04)
    for x in [-3.9,3.9]:
        for z in [-2.95,2.95]: box('Timber corner',(x,1.8,z),(.16,3.6,.16),'wood',.025)
    for side in [-1,1]:
        x=side*4.04
        for y in [1.05,3.05]: box('Side timber course',(x,y,0),(.12,.13,5.95),'wood_light',0)
        for z in [-1.65,1.65]:
            box('Side window surround',(x,2.03,z),(.16,1.35,1.1),'wood',.045)
            box('Side window recess',(x+side*.1,2.03,z),(.07,1.12,.86),'teal_dark',0)
            box('Side window mullion',(x+side*.145,2.03,z),(.05,1.1,.035),'gold',0)
            box('Side sill',(x+side*.16,1.3,z),(.4,.13,1.3),'stone',.025)
            for offset in [-.69,.69]:
                box('Woven shutter',(x+side*.08,2.03,z+offset),(.08,1.27,.32),'teal',.025)
                for h in [1.66,2.13]: box('Shutter strap',(x+side*.135,h,z+offset),(.04,.055,.32),'copper',0)
    for z in [-3.07,3.07]:
        outline=[(-4,3.05,z)]+[(x,5.15-1.83*(abs(x)/4.55)**.7,z) for x in [-4+i*.5 for i in range(17)]]+[(4,3.05,z)]
        face=tuple(range(len(outline)))
        mesh('Curved sail gable',outline,[face if z<0 else tuple(reversed(face))],'paper')
        orb('Loft lens',(0,4.05,z),(.32,.32,.07),'teal_dark',segments=16,rings=8)
        ring('Loft lens frame',(0,4.05,z),.34,.045,'copper',tilt=math.pi/2,segments=24)
        box('Top beam',(0,3.12,z),(8.25,.16,.18),'wood')
        box('Lower beam',(0,1.05,z),(8.12,.1,.12),'wood_light',.015)
        for x in [-2.5,2.5]:
            box('Window frame',(x,2.0,z),(1.25,1.48,.14),'wood',.07)
            box('Window recess',(x,2.03,z+.08*(1 if z>0 else -1)),(1.03,1.23,.07),'teal_dark',.05)
            box('Sill',(x,1.25,z+.17*(1 if z>0 else -1)),(1.45,.14,.36),'stone',.035)
            for offset in [-.21,.21]: box('Window mullion',(x+offset,2.01,z+.12*(1 if z>0 else -1)),(.045,1.22,.06),'gold',.006)
        box('Door arch',(0,1.28,z),(1.8,2.55,.12),'stone',.15)
        box('Door',(0,1.16,z+.08*(1 if z>0 else -1)),(1.34,2.25,.13),'teal_dark',.12)
        for x in [-.45,-.22,0,.22,.45]: box('Door plank',(x,1.16,z+.17*(1 if z>0 else -1)),(.025,2.0,.025),'teal',.003)
    # Layered teal roof tiles curve slightly upward at the eaves.
    for side in [-1,1]:
        for row in range(7):
            x0=side*row*.65; x1=side*(row+1)*.65
            y0=5.24-1.83*(row/7)**.7; y1=5.24-1.83*((row+1)/7)**.7
            for col in range(11):
                z=-3.5+col*.64+(row%2)*.1
                mesh('Overlapping roof tile',[(x0,y0,z),(x0,y0,z+.67),(x1,y1,z+.69),(x1,y1,z-.01),
                    (x1,y1-.065,z-.01),(x1,y1-.065,z+.69)],
                    [(0,1,2,3),(3,2,5,4),(1,0,3,2)], ['teal','teal_dark','teal_light'][(row+col*3)%7%3])
    beam('Roof ridge',(0,5.25,-3.65),(0,5.25,3.65),.1,'copper')
    for z in [-3.55,3.55]:
        for side in [-1,1]: beam('Roof edge',(0,5.27,z),(side*4.56,3.43,z),.075,'wood')
    box('Chimney',(-2.15,4.7,-1.1),(.68,1.7,.7),'stone',.045)
    box('Chimney cap',(-2.15,5.57,-1.1),(.87,.12,.91),'light_stone',.02)


def tree():
    points=[(0,0,0),(.14,1.6,.02),(-.12,2.7,.04),(.22,3.6,.06)]
    for i in range(3): beam('Curved trunk',points[i],points[i+1],.23-i*.048,'wood',.18-i*.05)
    for i in range(5):
        a=i*2.4
        b=(math.cos(a)*1.45,3.15+(i%3)*.38,math.sin(a)*1.15)
        beam('Branch',(.04,2.2,0),b,.105,'wood',.024)
        for j in range(5):
            angle=a+j*1.41
            center=(b[0]+math.cos(angle)*.53,b[1]+.15+(j%2)*.23,b[2]+math.sin(angle)*.51)
            orb('Shaped foliage',center,(.82,.36,.64),['leaf','leaf_light','leaf_dark'][(i+j)%3],segments=10,rings=5)
    # Long tapered sprays break up the silhouette instead of a spherical crown.
    for i in range(30):
        a=i*2.399
        radius=1.1+(i%4)*.22
        start=(math.cos(a)*radius,3.2+(i%5)*.13,math.sin(a)*radius*.8)
        leaf('Hanging reed leaf',start,(start[0]*1.08,start[1]-.65,start[2]*1.08),.18,'leaf_light' if i%3==0 else 'leaf')


def reeds():
    for i in range(11):
        a=i*2.399; x=math.cos(a)*.38; z=math.sin(a)*.38; height=.6+(i%5)*.15
        beam('Sunthread stem',(x,0,z),(x*.8,height,z*.8),.018,'leaf',.009,6)
        leaf('Reed blade',(x,.09,z),(x+.2,height*.65,z+.08),.06,'leaf_light')
        lathe('Sunthread seed',(x*.8,height,z*.8),[(.015,0),(.05,.05),(.045,.18),(.015,.24)],'gold',6)


def paving():
    # A single reusable irregular stone. Placement lives in the modular world scene.
    box('Worn paving',(0,.006,0),(.68,.028,.51),'stone',.07,rotation=.06)


def kit():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    objects=[]
    for name,recipe in [('LanternWell',well),('SupplyCart',cart),('Planter',planter),
                        ('LanternPost',lantern),('SailHouse',house),('WindTree',tree),
                        ('SunthreadCluster',reeds),('PavingStone',paving)]:
        objects.append(asset(name,recipe))
    export(objects,'dawnreef_kit')


PAINT=material('DawnreefPaint')
GLOW=material('LanternGlow',True)
if __name__=='__main__':
    kit()
