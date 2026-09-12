"""Transactional orchestration for catalog quest/dialogue rules supplied as a port."""
from backend.app.modules.vertical_slice.domain import LEVEL_XP_REQUIREMENT


class StoryService:
    def __init__(self, players, rules):
        self.players, self.rules = players, rules

    def _run(self, account_id, character_id, apply):
        with self.players.store.transaction(character_id):
            character = self.players._require_character(account_id, character_id)
            if character.encounter.get("state") == "active":
                raise ValueError("finish the encounter before interacting")
            result = apply(character)
            self._settle_level(character)
            self.players.store.save_character(character)
            return {"character": character.public_state(), **result}

    def start(self, account_id, character_id, npc_key):
        def apply(character):
            self.rules.advance(character, "talk_to_npc", npc_key)
            self._settle_level(character)
            return {"dialogue": self.rules.start_dialogue(character, npc_key)}
        return self._run(account_id, character_id, apply)

    @staticmethod
    def _settle_level(character):
        while character.experience >= LEVEL_XP_REQUIREMENT * character.level:
            character.level += 1

    def choose(self, account_id, character_id, npc_key, conversation_id, option_key):
        return self._run(account_id, character_id, lambda c: {
            "dialogue": self.rules.choose_dialogue(c, npc_key, conversation_id, option_key)})

    def inspect(self, account_id, character_id, interaction_key):
        return self._run(account_id, character_id, lambda c: {"discovery": self.rules.inspect(c, interaction_key)})
