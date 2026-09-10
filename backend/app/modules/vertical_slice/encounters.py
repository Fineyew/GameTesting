"""Owns aggregate transactions and reward receipts; combat is supplied as a port."""
from copy import deepcopy
import hashlib
import json
from uuid import uuid4


class EncounterService:
    def __init__(self, players, engine, catalog):
        self.players, self.engine, self.catalog = players, engine, catalog

    def _command(self, account_id, character_id, key, payload, apply):
        if not isinstance(key, str) or not 8 <= len(key) <= 80:
            raise ValueError("Idempotency-Key must contain 8–80 characters")
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with self.players.store.transaction(character_id):
            character = self.players._require_character(account_id, character_id)
            receipt = character.command_receipts.get(key)
            if receipt:
                if receipt["fingerprint"] != fingerprint:
                    raise ValueError("command key reused with a different action")
                return deepcopy(receipt["response"])
            apply(character)
            response = {"character": character.public_state(), "encounter": deepcopy(character.encounter)}
            character.command_receipts[key] = {"fingerprint": fingerprint, "response": response}
            # Old action retries also carry encounter id and expected round; pruning cannot grant rewards twice.
            while len(character.command_receipts) > 128:
                del character.command_receipts[next(iter(character.command_receipts))]
            self.players.store.save_character(character)
            return deepcopy(response)

    def start(self, account_id, character_id, enemy_key, key):
        def apply(character):
            if character.encounter.get("state") == "active":
                return
            if enemy_key != "fog_thorn_lurker":
                raise ValueError("encounter not available")
            character.encounter = self.engine.begin(enemy_key, character.vigor, character.known_spells)
            character.encounter["id"] = str(uuid4())
        return self._command(account_id, character_id, key, {"start": enemy_key}, apply)

    def act(self, account_id, character_id, encounter_id, action, expected_round, key):
        def apply(character):
            encounter = character.encounter
            if encounter.get("id") != encounter_id or encounter.get("round") != expected_round:
                raise ValueError("encounter changed; reload before acting")
            character.encounter = self.engine.resolve(encounter, action)
            character.vigor = character.encounter["player_vigor"]
            if character.encounter["state"] == "victory":
                self._reward(character, encounter["enemy_key"])
            elif character.encounter["state"] == "defeat":
                character.vigor = 30
                character.position = {"x": 0.0, "z": 4.0}
        payload = {"encounter_id": encounter_id, "action": action, "expected_round": expected_round}
        return self._command(account_id, character_id, key, payload, apply)

    def _reward(self, character, enemy_key):
        character.defeated_enemies[enemy_key] = character.defeated_enemies.get(enemy_key, 0) + 1
        character.experience += 25
        character.wallet["shell_chits"] = character.wallet.get("shell_chits", 0) + 2
        if self.players.quest_rules:
            self.players.quest_rules.advance(character, "defeat_enemy", enemy_key)
        else:
            self._legacy_quest_rewards(character, enemy_key)
        while character.experience >= 100 * character.level:
            character.level += 1

    def _legacy_quest_rewards(self, character, enemy_key):
        """Compatibility for standalone legacy service callers without injected rules."""
        for key, progress in character.quest_state.items():
            if progress.get("rewards_claimed") or progress.get("state") != "accepted":
                continue
            quest = self.catalog.get_definition("quests", key)
            for objective in quest.rules["objectives"]:
                if objective["type"] == "defeat_enemy" and objective["enemy_key"] == enemy_key:
                    progress["objectives"][objective["key"]] = min(objective["quantity"], progress["objectives"].get(objective["key"], 0) + 1)
            if not all(progress["objectives"].get(o["key"], 0) >= o["quantity"] for o in quest.rules["objectives"]):
                continue
            progress.update(state="completed", completed=True, rewards_claimed=True)
            for reward in quest.rules["rewards"]:
                kind = reward["type"]
                if kind == "grant_experience":
                    character.experience += reward["amount"]
                elif kind == "grant_currency":
                    currency = reward["currency_key"]
                    character.wallet[currency] = character.wallet.get(currency, 0) + reward["amount"]
                elif kind == "grant_item":
                    item = reward["item_key"]
                    character.inventory[item] = character.inventory.get(item, 0) + reward["quantity"]
