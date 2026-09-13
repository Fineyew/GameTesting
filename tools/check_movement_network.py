"""Deterministic network impairment schedule against the real Godot controller.

Python generates authoritative 20Hz positions; Godot predicts at 60Hz. This is a
reproducible controller test, not a claim of physical cellular-network measurement.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from backend.app.modules.world.simulation import step
from backend.app.modules.world.terrain import TerrainSurface

ROOT = Path(__file__).resolve().parents[1]


def fixtures():
    geometry=json.loads((ROOT/'content/zones/dawnreef_atoll.json').read_text())['rules']['world']
    surface=TerrainSurface(geometry['terrain'])
    cases=[]
    routes=[('ramp',[6,11],[0,.35]),('stairs',[6,18.5],[0,-.45]),
            ('wall',[-3,-3],[-.6,0]),('terrace_edge',[3,14.5],[.6,0])]
    for name,start,axis in routes:
        for delay in [3,9,18]: # one-way 50/150/300ms at60Hz
            for interruption in ['none','loss','rejoin']:
                position=start[:]; velocity=[0,0]; received=[0,0]; packet_at=0
                inputs={}; snapshots={}; states=[]
                for tick in range(420):
                    offline=interruption!='none' and 75<=tick<135
                    desired=axis if tick<120 else [0,0]
                    if tick%6==0 and not offline:
                        inputs[tick+delay]=desired
                    if tick in inputs:
                        received=inputs[tick]; packet_at=tick
                    if tick%3==0:
                        position,velocity=step(position,velocity,received if tick-packet_at<24 else [0,0],.05,geometry,surface)
                    server=[position[0],surface.sample(*position)['height'],position[1]]
                    if tick%6==0 and not offline:
                        snapshots[tick+delay]=server
                    # Rejoin explicitly seeds the first received state, as existing real WS tests exercise.
                    states.append({'axis':desired,'server':server,'snapshot':snapshots.get(tick),
                                   'connected':not (interruption=='rejoin' and offline),
                                   'reset':interruption=='rejoin' and tick==135})
                cases.append({'name':f'{name}_{delay*1000//60}ms_{interruption}','start':start,'frames':states})
    return {'geometry':geometry,'cases':cases}


def check():
    with tempfile.TemporaryDirectory() as temporary:
        fixture=Path(temporary)/'network.json'; fixture.write_text(json.dumps(fixtures()))
        result=subprocess.run([os.environ.get('GODOT_BIN','godot'),'--headless','--path',str(ROOT/'godot_project'),
            '--script','res://tests/movement_network.gd','--',str(fixture)],capture_output=True,text=True,timeout=45)
        output=result.stdout+result.stderr
        print(output)
        assert result.returncode==0 and 'MOVEMENT_NETWORK_PASS' in output and 'ERROR' not in output


if __name__=='__main__':check()
