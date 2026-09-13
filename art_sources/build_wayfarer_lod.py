"""Original distant meshes derived from the editable M1.4 sources, preserving the rig.
Blender 4.5.3: --background --factory-startup --python art_sources/build_wayfarer_lod.py
The near mesh, saved palette IDs and 13 named bones remain intact.
"""
from pathlib import Path
import sys
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_dawnreef import export
ROOT=Path(__file__).resolve().parents[1]

for role in ['wayfarer','mara']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art_sources/dawnreef'/f'{role}.blend'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active=body
    simplify=body.modifiers.new('Distant silhouette','DECIMATE')
    simplify.ratio=.16
    bpy.ops.object.modifier_move_up(modifier=simplify.name)
    bpy.ops.object.modifier_apply(modifier=simplify.name)
    body.data.validate(verbose=True)
    assert not body.data.validate(), "Distant mesh must be valid after duplicate-face cleanup"
    export([body,arm],role+'_far',save_source=False)
    body.data.calc_loop_triangles()
    print(f'DISTANT_RIG {role}: {len(body.data.loop_triangles)} triangles; {len(arm.data.bones)} bones')
