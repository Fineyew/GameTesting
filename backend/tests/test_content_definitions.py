import json
import unittest
from pathlib import Path


CONTENT_ROOT = Path(__file__).resolve().parents[2] / "content"

REQUIRED_CATEGORIES = {
    "achievements",
    "crafting",
    "dialogue",
    "dungeons",
    "enemies",
    "equipment",
    "items",
    "loot_tables",
    "mounts",
    "npcs",
    "quests",
    "shops",
    "spells",
    "zones",
}


class ContentDefinitionTests(unittest.TestCase):
    def test_required_content_categories_exist(self) -> None:
        missing = [category for category in REQUIRED_CATEGORIES if not (CONTENT_ROOT / category).is_dir()]
        self.assertEqual([], missing)

    def test_content_files_have_required_shape(self) -> None:
        content_files = sorted(CONTENT_ROOT.glob("*/*.json"))
        self.assertGreater(len(content_files), 0)

        seen_keys: set[tuple[str, str, int]] = set()
        for path in content_files:
            with self.subTest(path=path):
                payload = json.loads(path.read_text(encoding="utf-8"))

                self.assertEqual(path.parent.name, payload.get("type"))
                self.assertEqual(path.stem, payload.get("key"))
                self.assertIsInstance(payload.get("version"), int)
                self.assertGreaterEqual(payload["version"], 1)

                display = payload.get("display")
                self.assertIsInstance(display, dict)
                self.assertIsInstance(display.get("name"), str)
                self.assertTrue(display["name"])

                self.assertIsInstance(payload.get("rules", {}), dict)
                self.assertIsInstance(payload.get("assets", {}), dict)
                self.assertIsInstance(payload.get("tags", []), list)

                unique_key = (payload["type"], payload["key"], payload["version"])
                self.assertNotIn(unique_key, seen_keys)
                seen_keys.add(unique_key)


if __name__ == "__main__":
    unittest.main()
