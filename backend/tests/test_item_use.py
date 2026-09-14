"""Consumable authority, durable receipts, concurrency and non-wasting failure rules."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.tests.test_commerce import commerce_game, buy, SHOP
from backend.app.core.config import get_settings
from backend.app.modules.content.validation import validate_content_tree
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.commerce import CommerceService

WRAP = 'sunthread_bandage'

def use(game, revision=0, key='use-wrap-first', item=WRAP):
    _, _, commands, account, character = game
    return commands.use(account, character, item, revision, key)

def set_vigor(players, account, character, value):
    with players.store.transaction(character):
        record = players.enter_world(account, character)
        record.vigor = value
        players.store.save_character(record)

@pytest.mark.parametrize('vigor,after',[(0,12),(16,28),(29,30)])
def test_use_caps_healing_and_persists_exact_retry(commerce_game, vigor, after):
    players, _, commands, account, character = commerce_game
    set_vigor(players, account, character, vigor)
    original = players.enter_world(account, character)
    result = use(commerce_game)
    assert result['character']['vigor'] == after
    assert result['character']['max_vigor'] == 30
    assert result['character']['inventory'][WRAP] == original.inventory[WRAP]-1
    assert result['character']['commerce_revision'] == 1
    assert result['outcome']['restored'] == after-vigor
    restarted = VerticalSliceService(JsonVerticalSliceStore(players.store.path))
    resumed = CommerceService(restarted,commands.rules,lambda *_:False)
    assert resumed.use(account,character,WRAP,0,'use-wrap-first') == result
    assert restarted.enter_world(account,character).vigor == after
    assert restarted.enter_world(account,character).wallet == original.wallet
    assert restarted.enter_world(account,character).folio == original.folio


def test_invalid_unowned_full_active_and_forged_use_does_not_mutate(commerce_game):
    players, encounters, commands, account, character = commerce_game
    for item in ['forged','lanternkeeper_vest','clean_reed_cloth',None,True,[],{}]:
        before=players.store.path.read_bytes()
        with pytest.raises(ValueError):use(commerce_game,item=item)
        assert players.store.path.read_bytes()==before
    with pytest.raises(ValueError,match='does not belong'):
        commands.use('other-account',character,WRAP,0,'use-wrap-first')
    set_vigor(players,account,character,30)
    before=players.store.path.read_bytes()
    with pytest.raises(ValueError,match='already full'):use(commerce_game)
    assert players.store.path.read_bytes()==before
    encounters.start(account,character,'fog_thorn_lurker','use-active-start')
    before=players.store.path.read_bytes()
    with pytest.raises(ValueError,match='finish the encounter'):use(commerce_game)
    assert players.store.path.read_bytes()==before
    with players.store.transaction(character):
        record=players.enter_world(account,character);record.encounter={};record.vigor=12;record.inventory.pop(WRAP)
        players.store.save_character(record)
    with pytest.raises(ValueError,match='does not own'):use(commerce_game)


def test_use_rolls_back_and_rejects_stale_or_changed_replays(commerce_game, monkeypatch):
    players, _, commands, account, character = commerce_game
    before=players.store.path.read_bytes()
    with monkeypatch.context() as m:
        def fail():raise OSError('disk failure')
        m.setattr(players.store,'flush',fail)
        with pytest.raises(OSError):use(commerce_game)
    assert players.store.path.read_bytes()==before
    first=use(commerce_game)
    with ThreadPoolExecutor(4) as pool:
        assert all(r==first for r in pool.map(lambda _:use(commerce_game),range(4)))
    with pytest.raises(ValueError,match='different action'):use(commerce_game,item='clean_reed_cloth')
    with pytest.raises(ValueError,match='different action'):
        commands.equip(account,character,'chest',None,0,'use-wrap-first')
    with players.store.transaction(character):
        record=players.enter_world(account,character);record.command_receipts.clear();players.store.save_character(record)
    with pytest.raises(ValueError,match='changed'):use(commerce_game)
    assert players.enter_world(account,character).vigor==first['character']['vigor']


def test_simultaneous_use_purchase_and_last_wrap(commerce_game):
    players, _, commands, account, character = commerce_game
    set_vigor(players,account,character,0)
    def operation(index):
        try:
            return use(commerce_game) if index==0 else buy(commands,account,character,listing_key='buy_sunthread_bandage')
        except ValueError as error:
            assert 'changed' in str(error)
            return None
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(operation,range(2)))
    assert sum(r is not None for r in results)==1
    saved=players.enter_world(account,character)
    if results[0]:
        buy(commands,account,character,1,'buy-after-use',listing_key='buy_sunthread_bandage')
    else:use(commerce_game,1,'use-after-buy')
    saved=players.enter_world(account,character)
    assert saved.vigor==12 and saved.wallet['shell_chits']==9 and saved.inventory[WRAP]==2
    use(commerce_game,2,'use-second-wrap');use(commerce_game,3,'use-last-wrap')
    assert WRAP not in players.enter_world(account,character).inventory
    assert players.enter_world(account,character).vigor==30

@pytest.mark.parametrize('effects',[[{'type':'restore_vigor','amount':v}] for v in (True,-1,0,31,1.5,'12')]+[[{'type':'deal_damage','amount':12}],[{'type':'restore_vigor','amount':12}]*2])
def test_item_effect_validation(tmp_path,effects):
    root=tmp_path/'content';shutil.copytree(Path(__file__).resolve().parents[2]/'content',root)
    p=root/'items/sunthread_bandage.json';d=json.loads(p.read_text());d['rules']['use_effects']=effects;p.write_text(json.dumps(d))
    assert not validate_content_tree(root).is_valid


def test_item_use_api_rejects_authority_fields_and_replays(monkeypatch,tmp_path):
    monkeypatch.setenv('VT_PLAYER_STORE','json');monkeypatch.setenv('VT_VERTICAL_SLICE_SAVE_PATH',str(tmp_path/'api.json'));get_settings.cache_clear()
    from backend.app.main import create_app
    try:
        with TestClient(create_app()) as client:
            token=client.post('/api/v1/auth/register',json={'email':'wrap@example.test','display_name':'Wrap','password':'test-only-password'}).json()['access_token']
            headers={'Authorization':'Bearer '+token,'Idempotency-Key':'api-use-first'}
            record=client.post('/api/v1/characters',headers=headers,json={'name':'Wrap'}).json();identity=record['id']
            path=f'/api/v1/world/characters/{identity}/items/use';body={'item_key':WRAP,'expected_revision':0}
            assert client.post(path,json=body).status_code==401
            for extra in [{'amount':999},{'vigor':30},{'quantity':0},{'quantity':True},{'quantity':1},{'expected_revision':True},{'expected_revision':-1},{'item_key':1}]:
                assert client.post(path,headers=headers,json={**body,**extra}).status_code==422
            assert client.post(path,headers=headers,json=body).status_code==409
            players=client.app.state.vertical_slice_service;account=players.store.get_character(identity).account_id
            set_vigor(players,account,identity,20)
            result=client.post(path,headers=headers,json=body);assert result.status_code==200
            assert result.json()['outcome']['restored']==10
            assert client.post(path,headers=headers,json=body).json()==result.json()
            other=client.post('/api/v1/auth/register',json={'email':'wrap-other@example.test','display_name':'Other','password':'test-only-password'}).json()['access_token']
            assert client.post(path,headers={**headers,'Authorization':'Bearer '+other},json=body).status_code==403
            assert client.get('/api/v1/server-info').json()['item_use_protocol']==1
    finally:get_settings.cache_clear()
