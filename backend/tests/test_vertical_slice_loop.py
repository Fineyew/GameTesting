import tempfile
import unittest
from pathlib import Path

from backend.app.modules.vertical_slice.service import (
    STARTER_CURRENCY_KEY,
    STARTER_ENEMY_KEY,
    STARTER_ITEM_REWARD,
    STARTER_QUEST_KEY,
    VerticalSliceService,
)
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore


class VerticalSliceLoopTests(unittest.TestCase):
    def test_required_loop_persists_across_logout_and_login(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            save_path = Path(tmp_dir) / "slice_save.json"
            service = VerticalSliceService(JsonVerticalSliceStore(save_path))

            registered = service.register(
                email="player@example.test",
                display_name="Player",
                password="safe-password",
            )
            character = service.create_character(
                account_id=registered.account.id,
                name="Ari",
            )

            entered = service.enter_world(registered.account.id, character.id)
            self.assertEqual("dawnreef_atoll", entered.current_zone_key)
            self.assertEqual(1, entered.level)
            self.assertEqual({"glimmer_spark", "root_snare", "tide_mend"}, set(entered.known_spells))

            accepted = service.accept_quest(
                account_id=registered.account.id,
                character_id=character.id,
                quest_key=STARTER_QUEST_KEY,
            )
            self.assertEqual("accepted", accepted.quest_state[STARTER_QUEST_KEY]["state"])

            fight = service.fight_enemy(
                account_id=registered.account.id,
                character_id=character.id,
                enemy_key=STARTER_ENEMY_KEY,
                spell_key="root_snare",
            )
            self.assertTrue(fight.victory)
            self.assertEqual(100, fight.experience_gained)
            self.assertTrue(fight.level_gained)
            self.assertEqual(STARTER_QUEST_KEY, fight.quest_completed)
            self.assertEqual(2, fight.character.level)
            self.assertEqual(100, fight.character.experience)
            self.assertEqual(2, fight.character.inventory[STARTER_ITEM_REWARD])
            self.assertEqual(14, fight.character.wallet[STARTER_CURRENCY_KEY])
            self.assertEqual(
                "completed",
                fight.character.quest_state[STARTER_QUEST_KEY]["state"],
            )

            saved = service.save_progress(registered.account.id, character.id)
            self.assertEqual(2, saved.level)
            self.assertEqual({"status": "logged_out"}, service.logout(registered.account.id))

            reloaded_service = VerticalSliceService(JsonVerticalSliceStore(save_path))
            logged_in = reloaded_service.login("player@example.test", "safe-password")
            characters = reloaded_service.list_characters(logged_in.account.id)
            self.assertEqual(1, len(characters))

            loaded = reloaded_service.enter_world(logged_in.account.id, characters[0].id)
            self.assertEqual(2, loaded.level)
            self.assertEqual(100, loaded.experience)
            self.assertEqual(2, loaded.inventory[STARTER_ITEM_REWARD])
            self.assertEqual(14, loaded.wallet[STARTER_CURRENCY_KEY])
            self.assertEqual("completed", loaded.quest_state[STARTER_QUEST_KEY]["state"])
            self.assertEqual(1, loaded.defeated_enemies[STARTER_ENEMY_KEY])


if __name__ == "__main__":
    unittest.main()
