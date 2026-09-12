"""Editable, original Wayfarer/Mara mesh and three-clip rig for the M1.4 sample.
Blender 4.5.3: --background --factory-startup --python art_sources/build_wayfarer.py
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_dawnreef import bpy, xyz, box, beam, orb, ring, mesh, lathe, material, join_objects, export, PAINT, GLOW
import math


def bone(obj, name):
    group=obj.vertex_groups.new(name=name)
    group.add(list(range(len(obj.data.vertices))),1.0,'REPLACE')
    return obj


def cloth_shell(name, profile, mat, color='ffffff', split=False):
    n=20; verts=[]; faces=[]
    for rx,y,rz in profile:
        for i in range(n):
            a=i*math.tau/n
            h=y + (.065*math.cos(3*a) if split and y<.7 else 0)
            verts.append((rx*math.cos(a),h,rz*math.sin(a)))
    for j in range(len(profile)-1):
        for i in range(n):
            a=j*n+i; b=j*n+(i+1)%n
            faces.append((a,a+n,b+n,b))
    faces.append(tuple((len(profile)-1)*n+i for i in range(n)))
    obj=mesh(name,verts,faces,color,mat,smooth=True)
    hip=obj.vertex_groups.new(name='Pelvis')
    chest=obj.vertex_groups.new(name='Chest')
    for v in obj.data.vertices:
        weight=max(0,min(1,(v.co.z-.84)/.42))
        if weight>0: chest.add([v.index],weight,'REPLACE')
        if weight<1: hip.add([v.index],1-weight,'REPLACE')
    return obj


def build_character(role):
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for action in list(bpy.data.actions): bpy.data.actions.remove(action)
    robe=material('RobeTint')
    skin=material('SkinTint')
    mara=role=='mara'
    cloth_shell('Split travel coat',[(.30,.56,.22),(.265,.76,.205),(.22,.94,.18),(.245,1.20,.17),(.29,1.34,.18)],robe,split=True)
    cloth_shell('Woven shoulder mantle',[(.36,1.19,.25),(.38,1.31,.255),(.25,1.43,.19),(.13,1.45,.115)],PAINT,'paper')
    bone(orb('Neck',(0,1.45,0),(.098,.16,.095),'ffffff',skin),'Chest')
    bone(orb('Sculpted face',(0,1.66,-.025),(.232,.268,.209),'ffffff',skin,segments=24,rings=12),'Head')
    bone(orb('Jaw',(0,1.56,-.062),(.171,.14,.168),'ffffff',skin,segments=18,rings=8),'Head')
    for sign in [-1,1]:
        bone(orb('Ear',(sign*.226,1.63,.006),(.053,.085,.032),'ffffff',skin),'Head')
        bone(orb('Ear inset',(sign*.233,1.63,-.019),(.026,.052,.012),'coral',segments=12,rings=6),'Head')
        # Eyes face Godot -Z. Dark lashes and warm highlights stay legible at game distance.
        bone(orb('Eye socket',(sign*.089,1.68,-.217),(.079,.052,.024),'wood',segments=16,rings=8),'Head')
        bone(orb('Eye white',(sign*.089,1.677,-.231),(.065,.036,.012),'paper',segments=16,rings=8),'Head')
        bone(orb('Iris',(sign*.081,1.677,-.244),(.028,.032,.012),'teal_dark',segments=14,rings=8),'Head')
        bone(orb('Eye light',(sign*.081-.009,1.691,-.254),(.009,.01,.004),'ffffff',segments=10,rings=6),'Head')
        bone(beam('Expressive brow',(sign*.036,1.751,-.222),(sign*.148,1.756 if mara else 1.766,-.202),.018,'ink',.012,8),'Head')
        bone(orb('Cheek',(sign*.134,1.59,-.20),(.035,.018,.009),'coral',segments=12,rings=6),'Head')
    bone(orb('Nose',(0,1.629,-.227),(.042,.051,.055),'ffffff',skin,segments=14,rings=8),'Head')
    bone(beam('Mouth',(-.048,1.531,-.211),(.048,1.535,-.211),.01,'wood',.008,8),'Head')
    hair='665b56' if mara else '473b34'
    bone(orb('Hair cap',(0,1.80,.037),(.244,.174,.208),hair,segments=20,rings=10),'Head')
    for i in range(7):
        x=-.19+i*.06
        bone(orb('Swept hair lock',(x,1.819-abs(x)*.22,-.126+i*.011),(.073,.122,.1),hair,segments=12,rings=8),'Head')
    if mara:
        bone(orb('Braided bun',(0,1.79,.236),(.119,.116,.09),hair),'Head')
        bone(ring('Copper hair clasp',(0,1.8,.239),.115,.018,'copper',tilt=math.pi/2,segments=20),'Head')
        for i in range(3):
            bone(orb('Silver strand',(-.11+i*.05,1.91,.075),(.024,.04,.157),'paper',segments=10,rings=6),'Head')
        bone(box('Lanternwright apron',(0,.925,-.228),(.34,.59,.04),'coral',.04),'Pelvis')
        bone(box('Apron pocket',(.05,.96,-.264),(.21,.15,.026),'wood_light',.02),'Pelvis')
        bone(beam('Carpenter stylus',(.09,1.035,-.287),(.065,1.20,-.285),.013,'gold',.009,8),'Chest')
    else:
        # Short back mantle and split hem form an original, readable traveling silhouette.
        cape=mesh('Short traveling cape',[(-.28,1.36,.11),(.28,1.36,.11),(.30,.88,.23),(.19,.76,.26),(-.18,.83,.26),(-.31,.95,.23)],
                  [(0,1,2,3,4,5),(5,4,3,2,1,0)],'teal_dark')
        bone(cape,'Chest')
    # Belt and inset clasp.
    belt=cloth_shell('Leather belt',[(.23,.895,.20),(.235,.963,.20)],PAINT,'wood')
    bone(box('Buckle',(0,.928,-.207),(.14,.106,.025),'copper',.013),'Pelvis')
    bone(box('Buckle inset',(0,.928,-.226),(.074,.05,.015),'ink',.009),'Pelvis')
    # Travel sash and asymmetric folio pouch.
    bone(beam('Sash',(-.25,1.31,-.175),(.20,.98,-.194),.036,'wood',.028,8),'Chest')
    bone(box('Folio satchel',(.295,.865,.045),(.21,.29,.21),'wood',.045,rotation=.13),'Pelvis')
    bone(box('Satchel flap',(.312,.951,-.07),(.2,.12,.045),'wood_light',.024),'Pelvis')
    bone(orb('Satchel clasp',(.32,.919,-.102),(.026,.027,.013),'copper'),'Pelvis')
    # Small lens brooch, no copied emblem or school symbol.
    bone(ring('Lens brooch',(-.22,1.316,-.207),.057,.014,'gold',tilt=math.pi/2,segments=20),'Chest')
    bone(orb('Brooch glass',(-.22,1.316,-.214),(.028,.03,.012),'teal_light'),'Chest')
    for side,sign in [('L',-1),('R',1)]:
        arm=(sign*.30,1.29,0)
        elbow=(sign*.415,1.045,-.012)
        wrist=(sign*.445,.87,-.046)
        bone(beam('Upper sleeve',arm,elbow,.106,'ffffff',.085,12,robe),'UpperArm'+side)
        bone(orb('Shoulder',arm,(.112,.115,.112),'ffffff',robe),'UpperArm'+side)
        bone(beam('Fore sleeve',elbow,wrist,.086,'ffffff',.066,12,robe),'ForeArm'+side)
        bone(beam('Cuff',(sign*.44,.91,-.04),(sign*.45,.855,-.05),.077,'copper',.073,12),'ForeArm'+side)
        bone(orb('Hand',(sign*.447,.817,-.058),(.064,.093,.047),'ffffff',skin),'ForeArm'+side)
        bone(orb('Thumb',(sign*.399,.834,-.081),(.027,.044,.023),'ffffff',skin),'ForeArm'+side)
        hip=(sign*.13,.76,.015); knee=(sign*.13,.425,.015); ankle=(sign*.13,.135,.005)
        bone(beam('Trouser',hip,knee,.09,'ink',.074,12),'Thigh'+side)
        bone(beam('Boot shaft',knee,ankle,.078,'wood',.075,12),'Shin'+side)
        bone(box('Travel boot',(sign*.13,.09,-.074),(.173,.17,.29),'wood',.035),'Foot'+side)
        bone(box('Boot sole',(sign*.13,.035,-.078),(.18,.038,.303),'ink',.01),'Foot'+side)
        for h in [.2,.3]:
            bone(box('Boot strap',(sign*.13,h,-.06),(.15,.024,.045),'copper',.005),'Shin'+side)
    # Staff is carried by the existing left hand and uses the same cast identity.
    if not mara:
        bone(beam('Staff shaft',(-.465,.11,-.107),(-.465,1.73,-.107),.026,'wood_light',.018,10),'ForeArmL')
        for y in [1.45,1.51,1.57]:
            bone(ring('Staff binding',(-.465,y,-.107),.025,.012,'copper',segments=16),'ForeArmL')
        bone(ring('Staff lens',(-.465,1.84,-.107),.105,.024,'copper',tilt=math.pi/2,segments=24),'ForeArmL')
        bone(orb('Staff pearl',(-.465,1.84,-.108),(.057,.065,.038),'luminous',GLOW),'ForeArmL')
    meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
    body=join_objects(meshes,'MaraMesh' if mara else 'WayfarerMesh')
    bones={
        'Pelvis':((0,.76,0),(0,1.02,0),None),
        'Chest':((0,1.02,0),(0,1.42,0),'Pelvis'),
        'Head':((0,1.42,0),(0,1.85,0),'Chest'),
    }
    for side,sign in [('L',-1),('R',1)]:
        bones.update({
            'UpperArm'+side:((sign*.30,1.29,0),(sign*.415,1.045,-.012),'Chest'),
            'ForeArm'+side:((sign*.415,1.045,-.012),(sign*.447,.817,-.058),'UpperArm'+side),
            'Thigh'+side:((sign*.13,.76,.015),(sign*.13,.425,.015),'Pelvis'),
            'Shin'+side:((sign*.13,.425,.015),(sign*.13,.135,.005),'Thigh'+side),
            'Foot'+side:((sign*.13,.135,.005),(sign*.13,.07,-.20),'Shin'+side),
        })
    arm_data=bpy.data.armatures.new('WayfarerRig')
    arm=bpy.data.objects.new('WayfarerRig',arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True)
    bpy.context.view_layer.objects.active=arm
    bpy.ops.object.mode_set(mode='EDIT')
    for name,(head,tail,parent) in bones.items():
        b=arm_data.edit_bones.new(name); b.head=xyz(head); b.tail=xyz(tail)
        if parent: b.parent=arm_data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    modifier=body.modifiers.new('Wayfarer skin','ARMATURE'); modifier.object=arm
    body.parent=arm
    arm.animation_data_create()
    for name,length in [('Idle',48),('Walk',18),('Cast',24)]:
        action=bpy.data.actions.new(name)
        arm.animation_data.action=action
        for frame in range(0,length+1,3):
            phase=frame/length*math.tau
            for pb in arm.pose.bones:
                pb.rotation_mode='XYZ'; pb.rotation_euler=(0,0,0); pb.location=(0,0,0)
            if name=='Idle':
                arm.pose.bones['Chest'].rotation_euler.x=.016*math.sin(phase)
                arm.pose.bones['Head'].rotation_euler.y=.025*math.sin(phase)
                arm.pose.bones['Pelvis'].location.y=.005*math.sin(phase)
            elif name=='Walk':
                arm.pose.bones['Pelvis'].location.y=.025*(1-math.cos(phase*2))
                for side,sign in [('L',1),('R',-1)]:
                    swing=math.sin(phase)*sign
                    arm.pose.bones['Thigh'+side].rotation_euler.x=swing*.48
                    arm.pose.bones['Shin'+side].rotation_euler.x=-max(0,-swing)*.48
                    arm.pose.bones['Foot'+side].rotation_euler.x=-swing*.17
                    arm.pose.bones['UpperArm'+side].rotation_euler.x=-swing*(.13 if side=='L' else .25)
                    arm.pose.bones['ForeArm'+side].rotation_euler.x=-.08-max(0,swing)*.1
            else:
                lift=math.sin(frame/length*math.pi)**2
                arm.pose.bones['UpperArmL'].rotation_euler.x=-lift*.82
                arm.pose.bones['ForeArmL'].rotation_euler.x=-lift*.52
                arm.pose.bones['Chest'].rotation_euler.y=lift*.14
                arm.pose.bones['UpperArmR'].rotation_euler.x=lift*.22
            for pb in arm.pose.bones:
                pb.keyframe_insert(data_path='rotation_euler',frame=frame,group=pb.name)
                pb.keyframe_insert(data_path='location',frame=frame,group=pb.name)
        action.use_fake_user=True
        track=arm.animation_data.nla_tracks.new(); track.name=name
        track.strips.new(name,0,action)
        track.mute=True
    arm.animation_data.action=None
    for pb in arm.pose.bones:
        pb.rotation_euler=(0,0,0); pb.location=(0,0,0)
    bpy.context.scene.frame_set(0)
    bpy.context.scene.render.fps=24
    export([body,arm],role)


if __name__=='__main__':
    build_character('wayfarer')
    build_character('mara')
