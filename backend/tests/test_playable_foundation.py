import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.core.config import get_settings
from backend.app.core.passwords import hash_legacy_password, verify_password
from backend.app.core.security import decode_access_token
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.content.validation import validate_content_tree
from backend.app.modules.combat.engine import CombatEngine
from backend.app.modules.vertical_slice.encounters import EncounterService
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
from backend.app.modules.world.simulation import step

ROOT = Path(__file__).resolve().parents[2]

@pytest.fixture
def game(tmp_path):
    catalog = ContentCatalog.build(ROOT / 'content')
    players = VerticalSliceService(JsonVerticalSliceStore(tmp_path / 'save.json'))
    account = players.register('ari@example.test', 'Ari', 'a-safe-password').account
    character = players.create_character(account.id, 'Ari')
    return players, CombatEngine(catalog), EncounterService(players, CombatEngine(catalog), catalog), account.id, character.id


def test_heal_does_not_damage_enemy_or_mutate_original(game):
    _, engine, _, _, _ = game
    state = engine.begin('fog_thorn_lurker', 12, ['tide_mend'])
    result = engine.resolve(state, 'tide_mend')
    assert result['enemy_vigor'] == 32
    assert result['player_vigor'] == 16
    assert state['player_vigor'] == 12


def test_mark_and_binding_have_predictable_synergy(game):
    _, engine, _, _, _ = game
    state = engine.begin('fog_thorn_lurker', 30, ['beacon_trace', 'root_snare'])
    state = engine.resolve(state, 'beacon_trace')
    state = engine.resolve(state, 'root_snare')
    assert state['enemy_vigor'] == 20
    assert state['player_vigor'] == 20
    assert state['mark'] == 0


def test_reward_retry_after_reload_is_exactly_once(game):
    players, engine, encounters, account, character = game
    players.accept_quest(account, character, 'lantern_well_first_light')
    result = encounters.start(account, character, 'fog_thorn_lurker', 'start-0001')
    encounter_id = result['encounter']['id']
    for beat in range(1, 5):
        result = encounters.act(account, character, encounter_id, 'glimmer_spark', beat, f'action-000{beat}')
    assert result['encounter']['state'] == 'victory'
    assert result['character']['wallet']['shell_chits'] == 14
    reloaded = VerticalSliceService(JsonVerticalSliceStore(players.store.path))
    retry = EncounterService(reloaded, engine, engine.catalog).act(account, character, encounter_id, 'glimmer_spark', 4, 'action-0004')
    assert retry == result
    assert reloaded.enter_world(account, character).experience == 100
    with pytest.raises(ValueError, match='different action'):
        encounters.act(account, character, encounter_id, 'brace', 4, 'action-0004')


def test_concurrent_turns_cannot_spend_the_same_beat_twice(game):
    players, _, encounters, account, character = game
    result = encounters.start(account, character, 'fog_thorn_lurker', 'start-0001')
    def act(i):
        try:
            encounters.act(account, character, result['encounter']['id'], 'glimmer_spark', 1, f'action-000{i}')
            return True
        except ValueError:
            return False
    with ThreadPoolExecutor(4) as pool:
        assert sum(pool.map(act, range(4))) == 1
    assert players.enter_world(account, character).encounter['enemy_vigor'] == 24


def test_character_ownership_is_required(game):
    _, _, encounters, _, character = game
    with pytest.raises(ValueError, match='does not belong'):
        encounters.start('someone-else', character, 'fog_thorn_lurker', 'start-0001')


def test_invalid_action_rolls_back_disk_and_memory(game):
    players, _, encounters, account, character = game
    result = encounters.start(account, character, 'fog_thorn_lurker', 'start-0001')
    before = players.store.path.read_bytes()
    with pytest.raises(ValueError, match='not prepared'):
        encounters.act(account, character, result['encounter']['id'], 'invented_spell', 1, 'action-0001')
    assert players.store.path.read_bytes() == before
    assert players.enter_world(account, character).encounter['round'] == 1


def test_legacy_passwords_upgrade_and_logout_revokes_session(game):
    players, _, _, account, _ = game
    record = players.store.get_account(account)
    record.password_hash = hash_legacy_password('old-password')
    players.store.save_account(record)
    assert verify_password('old-password', record.password_hash)
    token = players.login(record.email, 'old-password').access_token
    assert players.store.get_account(account).password_hash.startswith('$argon2')
    players.logout(account)
    with pytest.raises(ValueError, match='session expired'):
        players.validate_session(decode_access_token(token))


def test_authority_blocks_buildings_and_zone_escape(game):
    geometry = game[1].catalog.get_definition('zones', 'dawnreef_atoll').rules['world']
    position, velocity = [0, 4], [0, 0]
    for _ in range(200):
        position, velocity = step(position, velocity, [1, 0], .05, geometry)
    assert position[0] <= 8.65
    for _ in range(400):
        position, velocity = step(position, velocity, [0, -1], .05, geometry)
    assert position[1] >= -21.65


def test_negative_focus_cost_rejected(tmp_path):
    import shutil
    shutil.copytree(ROOT / 'content', tmp_path / 'content')
    path = tmp_path / 'content/spells/glimmer_spark.json'
    definition = json.loads(path.read_text())
    definition['rules']['costs'][0]['amount'] = -1
    path.write_text(json.dumps(definition))
    assert not validate_content_tree(tmp_path / 'content').is_valid


def test_two_real_websockets_presence_chat_and_auth(monkeypatch, tmp_path):
    monkeypatch.setenv('VT_VERTICAL_SLICE_SAVE_PATH', str(tmp_path / 'web.json'))
    monkeypatch.setenv('VT_PLAYER_STORE', 'json')
    get_settings.cache_clear()
    from backend.app.main import create_app
    try:
        with TestClient(create_app()) as client:
            identities = []
            for i in range(2):
                response = client.post('/api/v1/auth/register', json={'email':f'player{i}@example.test','display_name':f'Player{i}','password':'safe-password'})
                assert response.status_code == 200
                token = response.json()['access_token']
                headers = {'Authorization': 'Bearer ' + token}
                response = client.post('/api/v1/characters', json={'name':f'Wayfarer{i}'}, headers=headers)
                assert response.status_code == 200
                identities.append((token, response.json()['id'], headers))
            with client.websocket_connect('/api/v1/world/socket') as a, client.websocket_connect('/api/v1/world/socket') as b:
                for socket, identity in zip([a,b], identities):
                    socket.send_json({'type':'auth','protocol':1,'token':identity[0],'character_id':identity[1]})
                    assert socket.receive_json()['type'] == 'welcome'
                frame = a.receive_json()
                while len(frame['players']) < 2:
                    frame = a.receive_json()
                assert len(frame['players']) == 2
                a.send_json({'type':'say','phrase':'hello'})
                for _ in range(10):
                    if any(p['bubble'] == 'Hello, Wayfarer!' for p in a.receive_json()['players']):
                        break
                else:
                    pytest.fail('chat bubble missing')
                assert client.post(f'/api/v1/world/characters/{identities[0][1]}/encounters', json={'enemy_key':'fog_thorn_lurker'}, headers=identities[0][2]).status_code == 422
                assert client.post('/api/v1/auth/logout', headers=identities[0][2]).status_code == 200
                assert client.get('/api/v1/characters', headers=identities[0][2]).status_code == 401
    finally:
        get_settings.cache_clear()
