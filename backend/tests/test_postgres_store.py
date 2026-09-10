"""Real database gates; skipped explicitly unless an isolated migrated database is supplied."""
import os
from pathlib import Path
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import text
from backend.app.db.player_store import PostgresPlayerStore
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.encounters import EncounterService
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.combat.engine import CombatEngine
from backend.app.modules.quests.rules import QuestRules
from backend.app.modules.vertical_slice.story import StoryService

pytestmark = pytest.mark.skipif(not os.environ.get('VT_TEST_DATABASE_URL'), reason='requires isolated PostgreSQL database')

@pytest.fixture
def game():
    store = PostgresPlayerStore(os.environ['VT_TEST_DATABASE_URL'])
    catalog = ContentCatalog.build(Path(__file__).resolve().parents[2]/'content')
    service = VerticalSliceService(store, QuestRules(catalog))
    key = uuid4().hex[:12]
    account = service.register(key+'@example.test', 'Tester '+key, 'test-only-password').account
    character = service.create_character(account.id, 'Reef '+key)
    yield service, EncounterService(service,CombatEngine(catalog),catalog), account.id, character.id
    with store.engine.begin() as connection:
        connection.execute(text('DELETE FROM character_runtime_states WHERE character_id = :id'),{'id':character.id})
        connection.execute(text('DELETE FROM characters WHERE id = :id'),{'id':character.id})
        connection.execute(text('DELETE FROM accounts WHERE id = :id'),{'id':account.id})
    store.engine.dispose()


def test_postgres_reward_is_durable_and_retry_safe(game):
    service, encounters, account, character = game
    service.accept_quest(account,character,'lantern_well_first_light')
    result=encounters.start(account,character,'fog_thorn_lurker','pg-start-0001')
    for beat in range(1,5):
        result=encounters.act(account,character,result['encounter']['id'],'glimmer_spark',beat,f'pg-action-{beat:04}')
    other=PostgresPlayerStore(os.environ['VT_TEST_DATABASE_URL'])
    try:
        loaded=other.get_character(character)
        assert loaded.wallet['shell_chits']==14 and loaded.level==2
        assert loaded.command_receipts['pg-action-0004']['response']==result
        assert encounters.act(account,character,result['encounter']['id'],'glimmer_spark',4,'pg-action-0004')==result
        assert other.get_character(character).wallet['shell_chits']==14
    finally:
        other.engine.dispose()


def test_postgres_serializes_concurrent_casts_and_rolls_back(game):
    service, encounters, account, character = game
    result=encounters.start(account,character,'fog_thorn_lurker','pg-start-0001')
    def cast(index):
        try:
            encounters.act(account,character,result['encounter']['id'],'glimmer_spark',1,f'pg-cast-{index:04}')
            return 1
        except ValueError:
            return 0
    with ThreadPoolExecutor(4) as pool:
        assert sum(pool.map(cast,range(4)))==1
    before=service.store.get_character(character)
    with pytest.raises(ValueError):
        with service.store.transaction(character):
            changed=service.store.get_character(character)
            changed.wallet['shell_chits']=999
            service.store.save_character(changed)
            raise ValueError('deliberate rollback')
    assert service.store.get_character(character)==before


def test_postgres_story_cursor_and_concurrent_turnin_are_durable(game):
    service, encounters, account, character = game
    story = StoryService(service, service.quest_rules)
    npc = 'mara_lanternwright'
    opened = story.start(account, character, npc)['dialogue']
    story.choose(account, character, npc, opened['id'], 'offer_help')
    result = encounters.start(account, character, 'fog_thorn_lurker', 'pg-story-start-0001')
    for beat in range(1,5):
        result = encounters.act(account, character, result['encounter']['id'], 'glimmer_spark', beat, f'pg-story-cast-{beat:04}')
    opened = story.start(account, character, npc)['dialogue']
    story.choose(account, character, npc, opened['id'], 'follow_note')
    story.inspect(account, character, 'sunthread_reeds')
    story.inspect(account, character, 'saltglass_cistern')
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: story.start(account, character, npc), range(4)))
    other = PostgresPlayerStore(os.environ['VT_TEST_DATABASE_URL'])
    try:
        saved = other.get_character(character)
        assert saved.wallet['shell_chits'] == 19 and saved.experience == 140
        assert saved.quest_state['an_answer_in_the_reeds']['rewards_claimed']
        assert saved.dialogue_state['node'] == 'answer_found'
        resumed = StoryService(VerticalSliceService(other, service.quest_rules), service.quest_rules)
        assert resumed.start(account, character, npc)['character']['wallet']['shell_chits'] == 19
    finally:
        other.engine.dispose()


def test_postgres_folio_acquisition_and_retry_after_reload(game):
    from backend.app.modules.vertical_slice.folio import FolioService
    from backend.tests.test_folio import finish_investigation, learn_field_spells, offer, LANCE
    service, encounters, account, character = game
    story = StoryService(service, service.quest_rules)
    finish_investigation((service, story, encounters, account, character))
    learn_field_spells(service, story, account, character)
    offer(story, account, character, LANCE)
    folio = FolioService(service, encounters.catalog)
    prepared = service.enter_world(account, character).known_spells
    updated = folio.prepare(account, character, prepared, 0, 'pg-folio-first')
    result = encounters.start(account, character, 'fog_thorn_lurker', 'pg-practice-start')
    for beat, action in enumerate(['beacon_trace','reed_aegis','gather','glimmer_spark','reed_aegis','tide_mend','glimmer_spark','reed_aegis','gather','glimmer_spark','reed_aegis','tide_mend','glimmer_spark'], 1):
        result = encounters.act(account, character, result['encounter']['id'], action, beat, f'pg-practice-{beat:04}')
    assert result['encounter']['state'] == 'victory'
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: story.start(account, character, 'mara_lanternwright'), range(4)))
    other = PostgresPlayerStore(os.environ['VT_TEST_DATABASE_URL'])
    try:
        resumed_players = VerticalSliceService(other, service.quest_rules)
        resumed = FolioService(resumed_players, encounters.catalog)
        assert resumed.prepare(account, character, prepared, 0, 'pg-folio-first') == updated
        loaded = other.get_character(character)
        assert loaded.known_spells.count('seam_lance') == 1 and len(loaded.known_spells) == 6
        assert loaded.folio == prepared and loaded.wallet['shell_chits'] == 21
        def prepare(index):
            try:
                resumed.prepare(account, character, ['seam_lance'], 1, f'pg-selection-{index:04}')
                return 1
            except ValueError:
                return 0
        with ThreadPoolExecutor(4) as pool:
            assert sum(pool.map(prepare, range(4))) == 1
        assert other.get_character(character).folio == ['seam_lance']
        assert other.get_character(character).folio_revision == 2
        combat = encounters.start(account, character, 'fog_thorn_lurker', 'pg-restricted-start')['encounter']
        with pytest.raises(ValueError, match='not prepared'):
            encounters.act(account, character, combat['id'], 'glimmer_spark', 1, 'pg-illegal-cast')
    finally:
        other.engine.dispose()


def test_postgres_old_payload_initializes_folio_without_reset(game):
    service, encounters, account, character = game
    service.accept_quest(account, character, 'lantern_well_first_light')
    active = encounters.start(account, character, 'fog_thorn_lurker', 'pg-old-save-start')
    before = service.enter_world(account, character)
    with service.store.engine.begin() as connection:
        connection.execute(text("UPDATE character_runtime_states SET payload = payload - 'folio' - 'folio_revision' WHERE character_id = :id"), {'id':character})
    other = PostgresPlayerStore(os.environ['VT_TEST_DATABASE_URL'])
    try:
        assert other.get_character(character) == before
        assert other.list_characters(account)[0].folio == before.known_spells
        result = encounters.act(account, character, active['encounter']['id'], 'glimmer_spark', 1, 'pg-old-save-cast')
        assert result['encounter']['round'] == 2
        assert other.get_character(character).folio == before.known_spells
    finally:
        other.engine.dispose()
