"""Story authority, migration compatibility, and once-only rewards across retries."""
import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.modules.combat.engine import CombatEngine
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.content.validation import validate_content_tree
from backend.app.modules.quests.rules import QuestRules
from backend.app.modules.vertical_slice.encounters import EncounterService
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
from backend.app.modules.vertical_slice.story import StoryService

ROOT = Path(__file__).resolve().parents[2]
NPC = "mara_lanternwright"
FIRST = "lantern_well_first_light"
FOLLOWUP = "an_answer_in_the_reeds"


@pytest.fixture
def story_game(tmp_path):
    catalog = ContentCatalog.build(ROOT / "content")
    rules = QuestRules(catalog)
    players = VerticalSliceService(JsonVerticalSliceStore(tmp_path / "story.json"), rules)
    account = players.register("story@example.test", "Listener", "test-only-password").account.id
    character = players.create_character(account, "Listener").id
    return players, StoryService(players, rules), EncounterService(players, CombatEngine(catalog), catalog), account, character


def accept_followup(game):
    players, story, encounters, account, character = game
    opened = story.start(account, character, NPC)["dialogue"]
    story.choose(account, character, NPC, opened["id"], "offer_help")
    combat = encounters.start(account, character, "fog_thorn_lurker", "story-start-0001")["encounter"]
    for beat in range(1, 5):
        encounters.act(account, character, combat["id"], "glimmer_spark", beat, f"story-cast-{beat:04}")
    assert players.enter_world(account, character).wallet["shell_chits"] == 14
    opened = story.start(account, character, NPC)["dialogue"]
    assert opened["node"] == "after_lurker"
    return story.choose(account, character, NPC, opened["id"], "follow_note")


def test_branch_cursor_rejects_forged_or_stale_choices(story_game):
    players, story, _, account, character = story_game
    opened = story.start(account, character, NPC)["dialogue"]
    before = players.store.path.read_bytes()
    with pytest.raises(ValueError, match="not available"):
        story.choose(account, character, NPC, opened["id"], "follow_note")
    assert players.store.path.read_bytes() == before
    branch = story.choose(account, character, NPC, opened["id"], "ask_well")["dialogue"]
    assert branch["node"] == "explain_well"
    with pytest.raises(ValueError, match="conversation changed"):
        story.choose(account, character, NPC, opened["id"], "offer_help")
    accepted = story.choose(account, character, NPC, branch["id"], "offer_help")
    assert accepted["character"]["quest_state"][FIRST]["state"] == "accepted"
    assert "dialogue_state" not in accepted["character"]


def test_prerequisites_ownership_and_combat_are_enforced(story_game):
    players, story, encounters, account, character = story_game
    with pytest.raises(ValueError, match="requirements"):
        with players.store.transaction(character):
            record = players.enter_world(account, character)
            players.quest_rules.accept(record, FOLLOWUP, NPC)
    assert FOLLOWUP not in players.enter_world(account, character).quest_state
    with pytest.raises(ValueError, match="does not belong"):
        story.start("another-account", character, NPC)
    encounters.start(account, character, "fog_thorn_lurker", "locked-start-0001")
    with pytest.raises(ValueError, match="finish the encounter"):
        story.inspect(account, character, "sunthread_reeds")


def test_ordered_discoveries_do_not_accept_early_or_repeated_events(story_game):
    players, story, _, account, character = story_game
    accept_followup(story_game)
    story.inspect(account, character, "saltglass_cistern")
    assert not any(players.enter_world(account, character).quest_state[FOLLOWUP]["objectives"].values())
    for _ in range(3):
        story.inspect(account, character, "sunthread_reeds")
    story.start(account, character, NPC)
    progress = players.enter_world(account, character).quest_state[FOLLOWUP]
    assert progress["objectives"] == {"hear_reeds": 1, "hear_cistern": 0, "tell_mara": 0}
    assert not progress["completed"]
    assert players.enter_world(account, character).wallet["shell_chits"] == 14


def test_concurrent_turnin_and_restart_cannot_duplicate_rewards(story_game):
    players, story, _, account, character = story_game
    accept_followup(story_game)
    story.inspect(account, character, "sunthread_reeds")
    story.inspect(account, character, "saltglass_cistern")
    with ThreadPoolExecutor(4) as pool:
        results = list(pool.map(lambda _: story.start(account, character, NPC), range(4)))
    assert all(r["dialogue"]["node"] == "answer_found" for r in results)
    reloaded = VerticalSliceService(JsonVerticalSliceStore(players.store.path), players.quest_rules)
    result = StoryService(reloaded, players.quest_rules).start(account, character, NPC)
    assert result["character"]["wallet"]["shell_chits"] == 19
    assert result["character"]["experience"] == 140
    assert result["character"]["quest_state"][FOLLOWUP]["rewards_claimed"]
    reloaded.accept_quest(account, character, FIRST)
    assert reloaded.enter_world(account, character).quest_state[FIRST]["completed"]


def test_old_saves_without_dialogue_cursor_load_unchanged(story_game):
    players, _, _, account, character = story_game
    payload = json.loads(players.store.path.read_text())
    payload["characters"][0].pop("dialogue_state")
    players.store.path.write_text(json.dumps(payload))
    restored = JsonVerticalSliceStore(players.store.path).get_character(character)
    assert restored.account_id == account and restored.dialogue_state == {}
    assert restored.inventory == players.enter_world(account, character).inventory


@pytest.mark.parametrize("mutation", ["negative_reward", "boolean_quantity", "missing_branch", "direct_reward", "malformed_conditions", "unknown_prerequisite"])
def test_authoring_rejects_unsafe_story_data(tmp_path, mutation):
    root = tmp_path / "content"
    shutil.copytree(ROOT / "content", root)
    category, key = ("dialogue", "mara_first_meeting") if mutation in {"missing_branch", "direct_reward"} else ("quests", FOLLOWUP)
    path = root / category / (key + ".json")
    data = json.loads(path.read_text())
    rules = data["rules"]
    if mutation == "negative_reward": rules["rewards"][0]["amount"] = -1
    elif mutation == "boolean_quantity": rules["objectives"][0]["quantity"] = True
    elif mutation == "missing_branch": rules["nodes"]["greeting"]["options"][0]["next_node"] = "invented"
    elif mutation == "direct_reward": rules["nodes"]["greeting"]["options"][0]["effects"] = [{"type": "grant_experience", "amount": 9999}]
    elif mutation == "malformed_conditions": rules["start_conditions"] = {"type": "quest_completed"}
    else: rules["start_conditions"][0]["quest_key"] = "invented"
    path.write_text(json.dumps(data))
    assert not validate_content_tree(root).is_valid


def test_story_api_requires_live_proximity_and_owner(monkeypatch, tmp_path):
    monkeypatch.setenv("VT_VERTICAL_SLICE_SAVE_PATH", str(tmp_path / "api.json"))
    monkeypatch.setenv("VT_PLAYER_STORE", "json")
    get_settings.cache_clear()
    from backend.app.main import create_app
    try:
        with TestClient(create_app()) as client:
            identities = []
            for index in range(2):
                token = client.post("/api/v1/auth/register", json={"email": f"story{index}@example.test", "display_name": "Listener", "password": "test-only-password"}).json()["access_token"]
                headers = {"Authorization": "Bearer " + token}
                character = client.post("/api/v1/characters", headers=headers, json={"name": f"Listener {index}"}).json()["id"]
                identities.append((token, character, headers))
            token, character, headers = identities[0]
            path = f"/api/v1/world/characters/{character}/npcs/{NPC}/dialogue"
            assert client.post(path).status_code == 401
            assert client.post(path, headers=identities[1][2]).status_code == 403
            assert client.post(path, headers=headers).status_code == 409
            with client.websocket_connect("/api/v1/world/socket") as socket:
                socket.send_json({"type": "auth", "protocol": 1, "token": token, "character_id": character})
                assert socket.receive_json()["type"] == "welcome"
                assert client.post(path, headers=headers, json={"position": [-4, -4]}).status_code == 409
                # Test setup owns the authoritative member; no API lets a client assign this position.
                client.app.state.world_hub.members[character].position = [-4, -4]
                response = client.post(path, headers=headers)
                assert response.status_code == 200
                conversation = response.json()["dialogue"]
                assert client.post(path + "/choose", headers=headers, json={"conversation_id": conversation["id"], "option_key": "follow_note"}).status_code == 409
                assert client.post(path + "/choose", headers=headers, json={"conversation_id": conversation["id"], "option_key": "offer_help"}).status_code == 200
                remote = f"/api/v1/world/characters/{character}/interactions/sunthread_reeds/inspect"
                assert client.post(remote, headers=headers, json={"completed": True}).status_code == 409
    finally:
        get_settings.cache_clear()
