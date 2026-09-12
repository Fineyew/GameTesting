"""Vendor/equipment orchestration on the existing locked character aggregate."""
from copy import deepcopy
import hashlib
import json


class CommerceService:
    def __init__(self, players, rules, near):
        self.players, self.rules, self.near = players, rules, near

    def _at_shop(self, character, shop_key):
        shop = self.rules.shop(shop_key)
        if character.current_zone_key != shop.rules["zone_key"] or not self.near(character.id, shop.rules["npc_key"]):
            raise ValueError("move close to Mara while connected")

    def view(self, account_id, character_id, shop_key=None):
        with self.players.store.transaction(character_id):
            character = self.players._require_character(account_id, character_id)
            if shop_key is not None:
                self._at_shop(character, shop_key)
                if character.encounter.get("state") == "active":
                    raise ValueError("finish the encounter before shopping")
                return self.rules.shop_view(character, shop_key)
            return self.rules.inventory_view(character)

    def _command(self, account_id, character_id, expected_revision, key, payload, apply):
        if not isinstance(key, str) or not 8 <= len(key) <= 80:
            raise ValueError("Idempotency-Key must contain 8–80 characters")
        if type(expected_revision) is not int or not 0 <= expected_revision < 2**63-1:
            raise ValueError("invalid commerce revision")
        payload = {"commerce": payload, "expected_revision": expected_revision}
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        with self.players.store.transaction(character_id):
            character = self.players._require_character(account_id, character_id)
            receipt = character.command_receipts.get(key)
            if receipt:
                if receipt["fingerprint"] != fingerprint:
                    raise ValueError("command key reused with a different action")
                return deepcopy(receipt["response"])
            if character.commerce_revision != expected_revision:
                raise ValueError("bag or equipment changed; reload before trying again")
            if character.encounter.get("state") == "active":
                raise ValueError("finish the encounter before changing supplies")
            outcome = apply(character)
            character.commerce_revision += 1
            response = {**self.rules.inventory_view(character), "outcome": outcome}
            character.command_receipts[key] = {"fingerprint": fingerprint, "response": response}
            # Permanent revision rejects stale commands even after response eviction.
            while len(character.command_receipts) > 128:
                del character.command_receipts[next(iter(character.command_receipts))]
            self.players.store.save_character(character)
            return deepcopy(response)

    def buy(self, account_id, character_id, shop_key, listing_key, quantity, shop_version, expected_revision, key):
        if not isinstance(listing_key, str) or not 1 <= len(listing_key) <= 64:
            raise ValueError("invalid listing")
        if type(quantity) is not int or not 1 <= quantity <= 10:
            raise ValueError("quantity must be an integer from 1 to 10")
        if type(shop_version) is not int or not 1 <= shop_version < 2**31:
            raise ValueError("invalid shop version")
        def apply(character):
            # Receipt replay is allowed after leaving the shop; new purchases require proximity.
            self._at_shop(character, shop_key)
            return self.rules.purchase(character, shop_key, listing_key, quantity, shop_version)
        return self._command(account_id, character_id, expected_revision, key,
                             {"buy": shop_key, "listing": listing_key, "quantity": quantity, "shop_version": shop_version}, apply)

    def equip(self, account_id, character_id, slot, item_key, expected_revision, key):
        if slot != "chest":
            raise ValueError("unknown equipment slot")
        if item_key is not None and (not isinstance(item_key, str) or not 1 <= len(item_key) <= 64):
            raise ValueError("invalid equipment item")
        def apply(character):
            if item_key is None:
                character.equipment.pop(slot, None)
            else:
                self.rules.equipment(character, slot, item_key)
                character.equipment[slot] = item_key
            return {"slot": slot, "item_key": item_key}
        return self._command(account_id, character_id, expected_revision, key,
                             {"equip": slot, "item_key": item_key}, apply)

    def use(self, account_id, character_id, item_key, expected_revision, key):
        if not isinstance(item_key, str) or not 1 <= len(item_key) <= 64:
            raise ValueError("invalid item")
        return self._command(account_id, character_id, expected_revision, key,
                             {"use": item_key}, lambda character: self.rules.use(character, item_key))
