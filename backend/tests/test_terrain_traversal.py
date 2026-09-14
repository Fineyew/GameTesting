import json
from pathlib import Path

import pytest

from backend.app.modules.world.terrain import TerrainSurface
from backend.app.modules.world.traversal import clear, move
from backend.app.modules.world.simulation import step
from backend.app.modules.world.protocol import geometry_digest

ROOT = Path(__file__).resolve().parents[2]


def world():
    return json.loads((ROOT/'content/zones/dawnreef_atoll.json').read_text())["rules"]["world"]


@pytest.mark.parametrize("height,allowed", [(300,True),(301,False),(-300,True),(-301,False)])
def test_step_limit_both_directions_and_small_inputs(height,allowed):
    surface = TerrainSurface({"bounds":[0,0,4,3],"cells":{"2:1":[height]*4}})
    pos = [1.5,1.5]
    for _ in range(150):
        pos,_ = move(surface,pos,[.01,0],[])
    assert (pos[0] > 2.5) == allowed
    if not allowed:
        assert pos[0] <= 1.65+1e-7


def test_swept_footprint_cannot_tunnel_through_thin_blocker():
    surface = TerrainSurface({"bounds":[0,0,4,4],"cells":{}})
    pos,stopped = move(surface,[1,1],[2,0],[[2,0,2.001,3]])
    assert pos[0] < 1.651 and stopped[0]


def test_blocked_axis_retains_tangential_travel():
    surface = TerrainSurface({"bounds":[0,0,4,4],"cells":{}})
    pos,stopped = move(surface,[1.6,1],[.5,.5],[[2,0,3,3]])
    assert pos[0] < 1.651 and pos[1] == pytest.approx(1.5)
    assert stopped == [True,False]


@pytest.mark.parametrize("rise,allowed", [(900,True),(901,False)])
def test_floor_angle_independent_of_tiny_tick(rise,allowed):
    surface = TerrainSurface({"bounds":[0,0,4,3],"cells":{"2:1":[0,rise,rise,0]}})
    assert clear(surface,[1.64,1.5],[1.66,1.5],[]) == allowed


def test_authored_route_ramp_terrace_steps_and_reverse():
    geometry=world(); surface=TerrainSurface(geometry['terrain'])
    pos,vel=[6,9],[0,0]
    top=0
    for _ in range(200):
        pos,vel=step(pos,vel,[0,1],.05,geometry,surface)
        top=max(top,surface.sample(*pos)['height'])
    assert pos[1]>18 and top == pytest.approx(1.2)
    for _ in range(200):
        pos,vel=step(pos,vel,[0,-1],.05,geometry,surface)
    assert pos[1]<9


def test_saved_position_clearance_and_nonlocation_state(tmp_path):
    from backend.app.modules.vertical_slice.service import VerticalSliceService
    from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
    from backend.app.modules.world.hub import WorldHub
    service=VerticalSliceService(JsonVerticalSliceStore(tmp_path/'save.json'))
    account=service.register('terrain@example.test','Terrain','safe-password').account.id
    character=service.create_character(account,'Terrain')
    hub=WorldHub(world(),service); service.position_validator=hub.safe_position
    with service.store.transaction(character.id):
        character.position={'x':6,'z':14.5}
        character.wallet['shell_chits']=17
        service.store.save_character(character)
    assert service.enter_world(account,character.id).position == {'x':6,'z':14.5}
    assert hub.height([6,14.5]) == 1.2
    with service.store.transaction(character.id):
        character.position={'x':5,'z':1000,'y':900}
        service.store.save_character(character)
    saved=service.enter_world(account,character.id)
    assert saved.position == {'x':0,'z':4} and saved.wallet['shell_chits']==17
    reloaded=JsonVerticalSliceStore(tmp_path/'save.json').get_character(character.id)
    assert reloaded.position == saved.position and reloaded.id == character.id


def test_digest_stable_across_integral_json_numeric_types():
    assert geometry_digest({'a':1,'b':[.35]}) == geometry_digest({'b':[.35],'a':1.0})
    assert geometry_digest({'a':1}) != geometry_digest({'a':2})


@pytest.mark.parametrize("displacement", [[3,0],[float('nan'),0],[True,0],[10**400,0]])
def test_forged_displacement_is_rejected(displacement):
    with pytest.raises(ValueError):
        move(TerrainSurface({'bounds':[0,0,4,4],'cells':{}}),[1,1],displacement,[])
