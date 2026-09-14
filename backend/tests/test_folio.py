"""Acquisition, ownership, durable preparation and combat legality across both adapters."""
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.modules.content.validation import validate_content_tree
from backend.app.modules.vertical_slice.domain import CharacterRecord, STARTING_SPELL_KEYS
from backend.app.modules.vertical_slice.folio import FolioService
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
from backend.app.modules.vertical_slice.story import StoryService
from backend.tests.test_story_progression import story_game, accept_followup, NPC, ROOT

TRACE = 'reading_the_afterlight'
AEGIS = 'what_the_reeds_hold'
LANCE = 'a_measured_release'


def offer(story, account, character, quest):
    cursor = story.start(account, character, NPC)['dialogue']
    return story.choose(account, character, NPC, cursor['id'], 'study_' + quest)


def learn_field_spells(players, story, account, character):
    """Continue a completed M1.1 save through actual validated offers/observations."""
    offer(story, account, character, TRACE)
    story.inspect(account, character, 'saltglass_cistern')
    story.start(account, character, NPC)
    offer(story, account, character, AEGIS)
    story.inspect(account, character, 'sunthread_reeds')
    return story.start(account, character, NPC)['character']


def finish_investigation(game):
    players, story, _, account, character = game
    accept_followup(game)
    story.inspect(account, character, 'sunthread_reeds')
    story.inspect(account, character, 'saltglass_cistern')
    story.start(account, character, NPC)


@pytest.fixture
def folio_game(story_game):
    players, story, encounters, account, character = story_game
    return (*story_game, FolioService(players, encounters.catalog))


def test_field_acquisition_is_gated_and_does_not_auto_prepare(folio_game):
    players, story, _, account, character, folio = folio_game
    with pytest.raises(ValueError, match='requirements'):
        players.quest_rules.accept(players.enter_world(account, character), TRACE, NPC)
    with pytest.raises(ValueError, match='not available'):
        offer(story, account, character, TRACE)
    finish_investigation(folio_game[:5])
    result = learn_field_spells(players, story, account, character)
    assert result['known_spells'] == [*STARTING_SPELL_KEYS, 'beacon_trace', 'reed_aegis']
    assert result['folio'] == list(STARTING_SPELL_KEYS)
    assert result['experience'] == 140 and result['wallet']['shell_chits'] == 19
    with pytest.raises(ValueError, match='does not know'):
        folio.prepare(account, character, ['seam_lance'], 0, 'unearned-lance')


@pytest.mark.parametrize('selection,message', [
    ([], 'between'), (['glimmer_spark'] * 7, 'between'),
    (['beacon_trace'], 'does not know'), (['invented'], 'unknown'),
    (['brace'], 'unknown'), (['gather'], 'unknown'),
    (['glimmer_spark', 'glimmer_spark'], 'duplicate'), ([True], 'unknown'),
    ([{'spell_key':'glimmer_spark'}], 'unknown'),
])
def test_forged_or_invalid_preparation_cannot_mutate_save(folio_game, selection, message):
    players, _, _, account, character, folio = folio_game
    before = players.store.path.read_bytes()
    with pytest.raises(ValueError, match=message):
        folio.prepare(account, character, selection, 0, 'invalid-folio')
    assert players.store.path.read_bytes() == before


def test_folio_retry_revision_and_ownership_survive_restart(folio_game):
    players, _, encounters, account, character, folio = folio_game
    first = folio.prepare(account, character, ['glimmer_spark'], 0, 'folio-first-01')
    folio.prepare(account, character, ['root_snare'], 1, 'folio-second-01')
    reloaded = VerticalSliceService(JsonVerticalSliceStore(players.store.path))
    resumed = FolioService(reloaded, encounters.catalog)
    assert resumed.prepare(account, character, ['glimmer_spark'], 0, 'folio-first-01') == first
    assert reloaded.enter_world(account, character).folio == ['root_snare']
    with pytest.raises(ValueError, match='different action'):
        resumed.prepare(account, character, ['tide_mend'], 0, 'folio-first-01')
    with pytest.raises(ValueError, match='does not belong'):
        resumed.prepare('other', character, ['glimmer_spark'], 0, 'folio-first-01')
    # A receipt may be pruned; the durable monotonic revision still rejects replay.
    with reloaded.store.transaction(character):
        record = reloaded.enter_world(account, character)
        record.command_receipts.clear()
        reloaded.store.save_character(record)
    with pytest.raises(ValueError, match='folio changed'):
        resumed.prepare(account, character, ['glimmer_spark'], 0, 'folio-first-01')


def test_concurrent_folio_updates_and_store_failure_are_atomic(folio_game, monkeypatch):
    players, _, _, account, character, folio = folio_game
    def prepare(index):
        try:
            folio.prepare(account, character, [STARTING_SPELL_KEYS[index % 3]], 0, f'concurrent-{index:04}')
            return 1
        except ValueError:
            return 0
    with ThreadPoolExecutor(4) as pool:
        assert sum(pool.map(prepare, range(4))) == 1
    before = players.enter_world(account, character)
    def fail():raise OSError('disk unavailable')
    monkeypatch.setattr(players.store, 'flush', fail)
    with pytest.raises(OSError):
        folio.prepare(account, character, ['tide_mend'], 1, 'failure-0001')
    assert players.enter_world(account, character) == before


def test_combat_uses_only_prepared_spells_and_universal_actions(folio_game):
    players, _, encounters, account, character, folio = folio_game
    folio.prepare(account, character, ['glimmer_spark'], 0, 'only-spark-0001')
    # The retained compatibility API cannot bypass preparation either.
    with pytest.raises(ValueError, match='not prepared'):
        players.fight_enemy(account, character, 'fog_thorn_lurker', 'root_snare')
    combat = encounters.start(account, character, 'fog_thorn_lurker', 'limited-start')['encounter']
    assert list(combat['spells']) == ['glimmer_spark']
    before = players.store.path.read_bytes()
    with pytest.raises(ValueError, match='not prepared'):
        encounters.act(account, character, combat['id'], 'root_snare', 1, 'not-prepared-01')
    assert players.store.path.read_bytes() == before
    with pytest.raises(ValueError, match='finish the encounter'):
        folio.prepare(account, character, ['root_snare'], 1, 'change-in-combat')
    result = encounters.act(account, character, combat['id'], 'brace', 1, 'universal-brace')
    assert result['encounter']['player_vigor'] == 30
    result = encounters.act(account, character, combat['id'], 'gather', 2, 'universal-gather')
    assert result['encounter']['focus'] == 6


def test_old_json_save_preserves_identity_progress_and_active_combat(folio_game):
    players, _, encounters, account, character, _ = folio_game
    finish_investigation(folio_game[:5])
    combat = encounters.start(account, character, 'fog_thorn_lurker', 'old-active-start')['encounter']
    before = players.enter_world(account, character)
    payload = json.loads(players.store.path.read_text())
    payload['characters'][0].pop('folio')
    payload['characters'][0].pop('folio_revision')
    players.store.path.write_text(json.dumps(payload))
    loaded = JsonVerticalSliceStore(players.store.path).get_character(character)
    assert asdict(loaded) == asdict(before)
    assert loaded.folio == list(STARTING_SPELL_KEYS) and loaded.folio_revision == 0
    assert encounters.engine.resolve(loaded.encounter, 'tide_mend')['round'] == combat['round'] + 1
    # Migration derives only already-owned spells, without granting new ones.
    small = asdict(before)
    small.pop('folio')
    small['known_spells'] = ['tide_mend']
    assert CharacterRecord(**small).folio == ['tide_mend']


def test_practice_requires_real_legal_casts_and_rewards_once(folio_game):
    players, story, encounters, account, character, folio = folio_game
    finish_investigation(folio_game[:5])
    learn_field_spells(players, story, account, character)
    offer(story, account, character, LANCE)
    prepared = [*STARTING_SPELL_KEYS, 'beacon_trace', 'reed_aegis']
    folio.prepare(account, character, prepared, 0, 'practice-folio')
    combat = encounters.start(account, character, 'fog_thorn_lurker', 'practice-start')['encounter']
    # Aegis before Trace, or on a weak intent, earns no lesson credit.
    def cast(action):
        state = players.enter_world(account, character).encounter
        return encounters.act(account, character, state['id'], action, state['round'], f'practice-{state["round"]:04}')
    cast('reed_aegis')
    assert players.enter_world(account, character).quest_state[LANCE]['objectives']['hold_pressure'] == 0
    cast('gather')
    cast('beacon_trace')
    cast('reed_aegis')
    assert players.enter_world(account, character).quest_state[LANCE]['objectives']['hold_pressure'] == 0
    held = cast('reed_aegis')
    assert held['character']['quest_state'][LANCE]['objectives']['hold_pressure'] == 1
    assert encounters.act(account, character, combat['id'], 'reed_aegis', 5, 'practice-0005') == held
    for action in ['tide_mend','glimmer_spark','reed_aegis','gather','glimmer_spark','reed_aegis','tide_mend','glimmer_spark','reed_aegis','gather','glimmer_spark']:
        result = cast(action)
    assert result['encounter']['state'] == 'victory'
    assert 'seam_lance' not in result['character']['known_spells']  # Report to the instructor.
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: story.start(account, character, NPC), range(4)))
    reloaded = VerticalSliceService(JsonVerticalSliceStore(players.store.path), players.quest_rules)
    saved = StoryService(reloaded, players.quest_rules).start(account, character, NPC)['character']
    assert saved['known_spells'].count('seam_lance') == 1
    assert saved['quest_state'][LANCE]['rewards_claimed']
    assert saved['experience'] == 165 and saved['wallet']['shell_chits'] == 21
    assert saved['folio'] == prepared
    selected = folio.prepare(account, character, saved['known_spells'], 1, 'all-six-folio')
    assert len(selected['character']['folio']) == 6


@pytest.mark.parametrize('reward', [
    {'type':'learn_spell','spell_key':'invented'}, {'type':'learn_spell'},
    {'type':'learn_spell','spell_key':'beacon_trace','quantity':2},
])
def test_invalid_acquisition_definition_rejected(tmp_path, reward):
    root = tmp_path / 'content'
    shutil.copytree(ROOT / 'content', root)
    path = root / 'quests' / (TRACE + '.json')
    data = json.loads(path.read_text())
    data['rules']['rewards'] = [reward]
    path.write_text(json.dumps(data))
    assert not validate_content_tree(root).is_valid


def test_folio_api_rejects_authority_fields_and_unowned_entries(monkeypatch, tmp_path):
    monkeypatch.setenv('VT_VERTICAL_SLICE_SAVE_PATH', str(tmp_path / 'api.json'))
    monkeypatch.setenv('VT_PLAYER_STORE', 'json')
    get_settings.cache_clear()
    from backend.app.main import create_app
    try:
        with TestClient(create_app()) as client:
            token = client.post('/api/v1/auth/register', json={'email':'folio@example.test','display_name':'Reader','password':'test-only-password'}).json()['access_token']
            headers = {'Authorization':'Bearer '+token, 'Idempotency-Key':'api-folio-first'}
            character = client.post('/api/v1/characters', headers=headers, json={'name':'Reader','known_spells':['seam_lance']}).json()
            assert character['known_spells'] == list(STARTING_SPELL_KEYS)
            path = f'/api/v1/world/characters/{character["id"]}/folio'
            assert client.post(path, json={'spells':['glimmer_spark'],'expected_revision':0}).status_code == 401
            for payload in [
                {'spells':['glimmer_spark'],'expected_revision':True},
                {'spells':['glimmer_spark'],'expected_revision':0,'known_spells':['seam_lance']},
            ]:
                assert client.post(path, headers=headers, json=payload).status_code == 422
            assert client.post(path, headers=headers, json={'spells':['seam_lance'],'expected_revision':0}).status_code == 409
            result = client.post(path, headers=headers, json={'spells':['glimmer_spark'],'expected_revision':0})
            assert result.status_code == 200
            assert result.json()['character']['folio'] == ['glimmer_spark']
            assert client.post(path, headers=headers, json={'spells':['glimmer_spark'],'expected_revision':0}).json() == result.json()
            assert client.get('/api/v1/server-info').json()['folio_protocol'] == 1
    finally:
        get_settings.cache_clear()
