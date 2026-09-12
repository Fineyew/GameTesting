import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app.core.config import get_settings
from backend.app.modules.world.hub import WorldHub, Presence


@pytest.fixture
def online(monkeypatch,tmp_path):
    monkeypatch.setenv('VT_PLAYER_STORE','json')
    monkeypatch.setenv('VT_VERTICAL_SLICE_SAVE_PATH',str(tmp_path/'save.json'))
    get_settings.cache_clear()
    from backend.app.main import create_app
    try:
        with TestClient(create_app()) as client:
            token=client.post('/api/v1/auth/register',json={'email':'terrain@example.test','display_name':'Terrain','password':'safe-password'}).json()['access_token']
            identity=client.post('/api/v1/characters',json={'name':'Terrain'},headers={'Authorization':'Bearer '+token}).json()['id']
            info=client.get('/api/v1/server-info').json()
            auth={'type':'auth','protocol':2,'geometry_revision':info['geometry_revision'],'geometry_digest':info['geometry_digest'],'token':token,'character_id':identity}
            yield client,auth
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize('change',[{'protocol':1},{'geometry_revision':1},{'geometry_digest':'0'*64},{'x':6,'y':999},{'character_id':'forged'}])
def test_reject_stale_geometry_forged_auth_and_other_character(online,change):
    client,auth=online
    with client.websocket_connect('/api/v1/world/socket') as socket:
        socket.send_json({**auth,**change})
        with pytest.raises(WebSocketDisconnect) as error:
            socket.receive_json()
        assert error.value.code in (4003,4004)


@pytest.mark.parametrize('packet',[
    {'type':'move','seq':1,'axis':[0,1],'y':100},
    {'type':'move','seq':1,'axis':[0,1],'position':[6,1.2,14]},
    {'type':'move','seq':True,'axis':[0,1]},
    {'type':'move','seq':1,'axis':[0,float('nan')]},
    {'type':'move','seq':1,'axis':[0,10**400]},
    [],
])
def test_forged_move_closes_without_accepting_height(online,packet):
    client,auth=online
    with client.websocket_connect('/api/v1/world/socket') as socket:
        socket.send_json(auth)
        assert socket.receive_json()['type']=='welcome'
        socket.send_text(json.dumps(packet))
        with pytest.raises(WebSocketDisconnect):
            for _ in range(20):socket.receive_json()


def test_snapshot_contract_and_stale_sequences(online):
    client,auth=online
    with client.websocket_connect('/api/v1/world/socket') as socket:
        socket.send_json(auth)
        welcome=socket.receive_json()
        assert welcome['protocol']==2 and welcome['geometry_digest']==auth['geometry_digest']
        frame=socket.receive_json()
        assert frame['players'][0]['y']==0
        assert frame['geometry_revision']==2
        hub=client.app.state.world_hub
        member=hub.members[auth['character_id']]
        hub.receive(member,{'type':'move','seq':10,'axis':[0,1]})
        member.last_packet-=.1
        hub.receive(member,{'type':'move','seq':9,'axis':[1,0]})
        assert member.seq==10 and member.axis==[0,1]
