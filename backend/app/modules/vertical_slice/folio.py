"""Prepared spells, serialized with the existing player aggregate and combat commands."""
from copy import deepcopy
import hashlib
import json

from backend.app.modules.vertical_slice.domain import FOLIO_CAPACITY


class FolioService:
    def __init__(self, players, catalog):
        self.players = players
        self.spells = {d.key for d in catalog.list_definitions("spells")}

    def prepare(self, account_id, character_id, spells, expected_revision, key):
        if not isinstance(key, str) or not 8 <= len(key) <= 80:
            raise ValueError("Idempotency-Key must contain 8–80 characters")
        if type(expected_revision) is not int or expected_revision < 0:
            raise ValueError("invalid folio revision")
        if not isinstance(spells, list) or not 1 <= len(spells) <= FOLIO_CAPACITY:
            raise ValueError("prepare between 1 and 6 spells")
        if any(not isinstance(s, str) or s not in self.spells for s in spells):
            raise ValueError("unknown spell selection")
        if len(set(spells)) != len(spells):
            raise ValueError("duplicate spell selection")
        fingerprint = hashlib.sha256(json.dumps({"folio": spells, "expected_revision": expected_revision}, sort_keys=True).encode()).hexdigest()
        with self.players.store.transaction(character_id):
            character = self.players._require_character(account_id, character_id)
            receipt = character.command_receipts.get(key)
            if receipt:
                if receipt["fingerprint"] != fingerprint:
                    raise ValueError("command key reused with a different action")
                return deepcopy(receipt["response"])
            if character.folio_revision != expected_revision:
                raise ValueError("folio changed; reload before preparing")
            if character.encounter.get("state") == "active":
                raise ValueError("finish the encounter before preparing spells")
            if any(s not in character.known_spells for s in spells):
                raise ValueError("character does not know that spell")
            character.folio = list(spells)
            character.folio_revision += 1
            response = {"character": character.public_state()}
            character.command_receipts[key] = {"fingerprint": fingerprint, "response": response}
            # Revision checks also reject late retries after receipt pruning.
            while len(character.command_receipts) > 128:
                del character.command_receipts[next(iter(character.command_receipts))]
            self.players.store.save_character(character)
            return deepcopy(response)
