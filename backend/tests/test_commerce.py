"""Earned purchases, equipment authority and aggregate retry/concurrency regressions."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import json
from pathlib import Path
import shutil

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.content.validation import validate_content_tree
from backend.app.modules.inventory.rules import InventoryRules
from backend.app.modules.vertical_slice.commerce import CommerceService
from backend.app.modules.vertical_slice.encounters import EncounterService
from backend.app.modules.combat.engine import CombatEngine
from backend.app.modules.quests.rules import QuestRules
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore

ROOT = Path(__file__).resolve().parents[2]
SHOP = 'dawnreef_supply_cart'
VEST = 'lanternkeeper_vest'
LISTING = 'buy_lanternkeeper_vest'


def earn_first_reward(players, encounters, account, character):
    players.accept_quest(account, character, 'lantern_well_first_light')
    result = encounters.start(account, character, 'fog_thorn_lurker', 'earn-chits-start')
    for beat in range(1, 5):
        result = encounters.act(account, character, result['encounter']['id'], 'glimmer_spark', beat, f'earn-chits-{beat:04}')
    assert result['character']['wallet']['shell_chits'] == 14


@pytest.fixture
def commerce_game(tmp_path):
    catalog = ContentCatalog.build(ROOT/'content')
    players = VerticalSliceService(JsonVerticalSliceStore(tmp_path/'players.json'), QuestRules(catalog))
    account = players.register('supplier@example.test', 'Supplier', 'test-only-password').account.id
    character = players.create_character(account, 'Supplier').id
    rules = InventoryRules(catalog)
    encounters = EncounterService(players, CombatEngine(catalog), catalog, rules)
    commerce = CommerceService(players, rules, lambda *_: True)
    earn_first_reward(players, encounters, account, character)
    return players, encounters, commerce, account, character


def buy(commerce, account, character, revision=0, key='first-purchase', **changes):
    args = dict(shop_key=SHOP, listing_key=LISTING, quantity=1, shop_version=2, expected_revision=revision, key=key)
    args.update(changes)
    return commerce.buy(account, character, **args)


def test_purchase_comparison_equip_unequip_and_json_restart(commerce_game):
    players, encounters, commerce, account, character = commerce_game
    original = players.enter_world(account, character)
    offer = commerce.view(account, character, SHOP)['shop']['listings'][0]
    assert offer['can_buy'] and offer['price'] == 12 and offer['guard_delta'] == 1
    purchased = buy(commerce, account, character)
    assert purchased['character']['wallet']['shell_chits'] == 2
    assert purchased['character']['inventory'][VEST] == 1
    assert not purchased['character']['equipment'] and purchased['stats']['guard'] == 0
    equipped = commerce.equip(account, character, 'chest', VEST, 1, 'first-equip-01')
    assert equipped['stats']['guard'] == 1
    assert equipped['character']['appearance'] == original.appearance
    other = VerticalSliceService(JsonVerticalSliceStore(players.store.path))
    resumed = CommerceService(other, commerce.rules, lambda *_: False)
    assert other.enter_world(account, character).equipment == {'chest': VEST}
    # Matching receipts remain valid after leaving the vendor and after another command.
    assert buy(resumed, account, character) == purchased
    assert resumed.equip(account, character, 'chest', VEST, 1, 'first-equip-01') == equipped
    assert resumed.view(account, character)['stats']['guard'] == 1
    removed = resumed.equip(account, character, 'chest', None, 2, 'unequip-first')
    assert removed['stats']['guard'] == 0 and removed['character']['inventory'][VEST] == 1
    assert JsonVerticalSliceStore(players.store.path).get_character(character).equipment == {}
    assert other.enter_world(account, character).known_spells == original.known_spells
    assert other.enter_world(account, character).folio == original.folio


@pytest.mark.parametrize('quantity', [0, -1, 11, 2**63, True, 1.0, '1', None, {}, []])
def test_malformed_quantity_never_mutates(commerce_game, quantity):
    players, _, commerce, account, character = commerce_game
    before = players.store.path.read_bytes()
    with pytest.raises(ValueError, match='quantity'):
        buy(commerce, account, character, quantity=quantity)
    assert players.store.path.read_bytes() == before


def test_purchase_forgery_unavailable_funds_stack_and_proximity(commerce_game):
    players, _, commerce, account, character = commerce_game
    before = players.store.path.read_bytes()
    for changes, message in [({'listing_key':'forged'}, 'not available'),
                             ({'listing_key':'buy_sunthread_bandage'}, 'not available'),
                             ({'shop_key':'forged'}, 'unavailable'),
                             ({'shop_version':1}, 'shop changed'),
                             ({'quantity':2}, 'full')]:
        with pytest.raises(ValueError, match=message):
            buy(commerce, account, character, **changes)
        assert players.store.path.read_bytes() == before
    commerce.near = lambda *_: False
    with pytest.raises(ValueError, match='close to Mara'):
        buy(commerce, account, character)
    commerce.near = lambda *_: True
    with players.store.transaction(character):
        record = players.enter_world(account, character)
        record.wallet['shell_chits'] = 11
        players.store.save_character(record)
    before = players.store.path.read_bytes()
    with pytest.raises(ValueError, match='not enough'):
        buy(commerce, account, character)
    assert players.store.path.read_bytes() == before


def test_receipt_conflicts_stale_commands_eviction_and_ownership(commerce_game):
    players, _, commerce, account, character = commerce_game
    first = buy(commerce, account, character)
    with ThreadPoolExecutor(4) as pool:
        assert all(result == first for result in pool.map(lambda _: buy(commerce, account, character), range(4)))
    for changes in [{'quantity':2}, {'shop_version':1}]:
        with pytest.raises(ValueError, match='different action'):
            buy(commerce, account, character, **changes)
    with pytest.raises(ValueError, match='does not belong'):
        buy(commerce, 'another-account', character)
    with pytest.raises(ValueError, match='different action'):
        commerce.equip(account, character, 'chest', VEST, 0, 'first-purchase')
    with players.store.transaction(character):
        record = players.enter_world(account, character)
        record.command_receipts.clear()
        players.store.save_character(record)
    with pytest.raises(ValueError, match='changed'):
        buy(commerce, account, character)
    assert players.enter_world(account, character).wallet['shell_chits'] == 2
    with pytest.raises(ValueError, match='already owned'):
        buy(commerce, account, character, revision=1, key='second-purchase')


def test_concurrent_purchases_cannot_overspend(commerce_game):
    players, _, commerce, account, character = commerce_game
    # Repeatable supply fixture exercises balance exhaustion beyond a unique gear cap.
    # The shipped bandage listing remains unavailable until item use exists.
    commerce.rules.shops[SHOP].rules['listings'][1]['available'] = True
    def purchase(index):
        for attempt in range(5):
            revision = players.enter_world(account, character).commerce_revision
            try:
                buy(commerce, account, character, revision, f'concurrent-{index}-{attempt}', listing_key='buy_sunthread_bandage')
                return 1
            except ValueError as error:
                if 'changed' not in str(error):
                    return 0
        return 0
    with ThreadPoolExecutor(4) as pool:
        assert sum(pool.map(purchase, range(4))) == 2
    saved = JsonVerticalSliceStore(players.store.path).get_character(character)
    assert saved.wallet['shell_chits'] == 4
    assert saved.inventory['sunthread_bandage'] == 4  # creation + quest + two purchases
    assert saved.commerce_revision == 2


def test_write_failure_rolls_back_charge_item_equipment_and_receipt(commerce_game, monkeypatch):
    players, _, commerce, account, character = commerce_game
    before = players.enter_world(account, character)
    disk = players.store.path.read_bytes()
    def fail(): raise OSError('deliberate disk failure')
    with monkeypatch.context() as patch:
        patch.setattr(players.store, 'flush', fail)
        with pytest.raises(OSError):
            buy(commerce, account, character)
    assert players.enter_world(account, character) == before and players.store.path.read_bytes() == disk
    buy(commerce, account, character)
    before = players.enter_world(account, character)
    with monkeypatch.context() as patch:
        patch.setattr(players.store, 'flush', fail)
        with pytest.raises(OSError):
            commerce.equip(account, character, 'chest', VEST, 1, 'failed-equip-01')
    assert players.enter_world(account, character) == before


def test_equipment_legality_combat_guard_and_active_lock(commerce_game):
    players, encounters, commerce, account, character = commerce_game
    for slot, item in [('chest',VEST), ('head',VEST), ('chest','sunthread_bandage'), ('chest','forged')]:
        with pytest.raises(ValueError):
            commerce.equip(account, character, slot, item, 0, 'invalid-equip')
    buy(commerce, account, character)
    commerce.rules.items[VEST].rules['required_level'] = 3
    with pytest.raises(ValueError, match='level'):
        commerce.equip(account, character, 'chest', VEST, 1, 'too-low-level')
    commerce.rules.items[VEST].rules['required_level'] = 1
    commerce.equip(account, character, 'chest', VEST, 1, 'valid-equip-01')
    combat = encounters.start(account, character, 'fog_thorn_lurker', 'guard-encounter')['encounter']
    assert combat['equipment_guard'] == 1 and len(combat['spells']) == 3
    cast = encounters.act(account, character, combat['id'], 'gather', 1, 'guard-gather-01')['encounter']
    assert cast['player_vigor'] == combat['player_vigor'] - 3
    cast = encounters.act(account, character, combat['id'], 'brace', 2, 'guard-brace-02')['encounter']
    assert cast['player_vigor'] == combat['player_vigor'] - 6  # 10 - Brace6 - gear1
    with pytest.raises(ValueError, match='finish the encounter'):
        commerce.equip(account, character, 'chest', None, 2, 'combat-unequip')
    with pytest.raises(ValueError, match='finish the encounter'):
        buy(commerce, account, character, 2, 'combat-purchase')
    # Saves made before equipment snapshots still resolve with zero gear protection.
    old = dict(combat); old.pop('equipment_guard')
    assert encounters.engine.resolve(old, 'gather')['player_vigor'] == combat['player_vigor'] - 4


def test_old_json_save_defaults_only_new_fields(commerce_game):
    players, encounters, _, account, character = commerce_game
    encounters.start(account, character, 'fog_thorn_lurker', 'old-active-encounter')
    before = asdict(players.enter_world(account, character))
    payload = json.loads(players.store.path.read_text())
    payload['characters'][0].pop('commerce_revision')
    payload['characters'][0].pop('equipment')
    players.store.path.write_text(json.dumps(payload))
    assert asdict(JsonVerticalSliceStore(players.store.path).get_character(character)) == before


@pytest.mark.parametrize('category,rule,value', [
    ('shops','listings',[]), ('shops','listings',[{'key':'broken'}]),
    ('equipment','modifiers',[{'stat':'damage','operation':'add','value':999}]),
    ('equipment','stack_limit',True), ('equipment','required_level',-1),
    ('shops','listings',[{'key':'vest','item_key':VEST,'quantity':1,'available':True,'price':[{'currency_key':'shell_chits','amount':-1}]}]),
    ('shops','listings',[{'key':'vest','item_key':VEST,'quantity':1,'available':True,'price':[{'currency_key':'shell_chits','amount':True}]}]),
    ('shops','listings',[{'key':'vest','item_key':VEST,'quantity':1,'available':True,'price':[{'currency_key':'shell_chits','amount':2**63}]}]),
    ('shops','listings',[{'key':'vest','item_key':VEST,'quantity':1,'available':True,'price':[{'currency_key':'forged','amount':1}]}]),
    ('shops','listings',[{'key':'vest','item_key':'forged','quantity':1,'available':True,'price':[{'currency_key':'shell_chits','amount':1}]}]),
])
def test_invalid_commerce_content_is_rejected(tmp_path, category, rule, value):
    root = tmp_path/'content'; shutil.copytree(ROOT/'content', root)
    path = root/category/((SHOP if category == 'shops' else VEST)+'.json')
    data = json.loads(path.read_text()); data['rules'][rule] = value
    path.write_text(json.dumps(data))
    assert not validate_content_tree(root).is_valid


def test_api_rejects_client_authority_fields_and_requires_owner_proximity(monkeypatch, tmp_path):
    monkeypatch.setenv('VT_VERTICAL_SLICE_SAVE_PATH',str(tmp_path/'api.json'))
    monkeypatch.setenv('VT_PLAYER_STORE','json'); get_settings.cache_clear()
    from backend.app.main import create_app
    try:
        with TestClient(create_app()) as client:
            token = client.post('/api/v1/auth/register',json={'email':'shop@example.test','display_name':'Shopper','password':'test-only-password'}).json()['access_token']
            headers = {'Authorization':'Bearer '+token,'Idempotency-Key':'api-purchase-01'}
            record = client.post('/api/v1/characters',headers=headers,json={'name':'Shopper','equipment':{'chest':VEST},'wallet':{'shell_chits':999}}).json()
            assert record['equipment'] == {} and record['wallet']['shell_chits'] == 0
            character = record['id']; path = f'/api/v1/world/characters/{character}'
            body = dict(listing_key=LISTING,quantity=1,shop_version=2,expected_revision=0)
            assert client.post(path+'/shops/'+SHOP+'/buy',json=body).status_code == 401
            assert client.post(path+'/shops/'+SHOP+'/buy',headers=headers,json=body).status_code == 409
            for extra in [{'price':0},{'item_key':'forged'},{'wallet':{}},{'quantity':True},{'quantity':'1'},{'quantity':1.0},{'expected_revision':True}]:
                assert client.post(path+'/shops/'+SHOP+'/buy',headers=headers,json={**body,**extra}).status_code == 422
            players = client.app.state.vertical_slice_service
            account = players.store.get_character(character).account_id
            earn_first_reward(players,client.app.state.encounters,account,character)
            # Proximity boundary is separately tested above and with real WS in online.gd.
            client.app.state.commerce.near = lambda *_: True
            assert client.post(path+'/shops/'+SHOP+'/buy',headers=headers,json={**body,'listing_key':'forged'}).status_code == 409
            result = client.post(path+'/shops/'+SHOP+'/buy',headers=headers,json=body)
            assert result.status_code == 200
            assert client.post(path+'/shops/'+SHOP+'/buy',headers=headers,json=body).json() == result.json()
            equipment = dict(slot='chest',item_key=VEST,expected_revision=1)
            headers['Idempotency-Key'] = 'api-equipment-01'
            assert client.post(path+'/equipment',headers=headers,json={**equipment,'guard':1000}).status_code == 422
            assert client.post(path+'/equipment',headers=headers,json=equipment).json()['stats']['guard'] == 1
            other = client.post('/api/v1/auth/register',json={'email':'other@example.test','display_name':'Other','password':'test-only-password'}).json()['access_token']
            headers['Authorization'] = 'Bearer '+other
            assert client.get(path+'/equipment',headers=headers).status_code == 403
            assert client.get(path+'/shops/'+SHOP,headers=headers).status_code == 403
            assert client.post(path+'/equipment',headers=headers,json=equipment).status_code == 403
            headers['Idempotency-Key'] = 'api-purchase-01'
            assert client.post(path+'/shops/'+SHOP+'/buy',headers=headers,json=body).status_code == 403
            assert client.get('/api/v1/server-info').json()['commerce_protocol'] == 1
    finally:
        get_settings.cache_clear()
