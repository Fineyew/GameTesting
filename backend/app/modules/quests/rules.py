"""Catalog-owned quest/dialogue rules. Call only inside a player-store transaction.

No transport, database, or client-declared progress enters this module. The caller
validates ownership and live proximity before supplying an interaction event.
"""
from copy import deepcopy
from uuid import uuid4

from backend.app.modules.contracts import ContentReader


class QuestRules:
    def __init__(self, catalog: ContentReader):
        self.definitions = {(d.type, d.key): d for d in catalog.list_definitions()}

    def definition(self, category, key):
        definition = self.definitions.get((category, key))
        if definition is None:
            raise ValueError("unknown content")
        return definition

    def conditions_met(self, character, conditions):
        for condition in conditions:
            kind = condition["type"]
            if kind == "character_level_at_least":
                passed = character.level >= condition["value"]
            elif kind == "quest_completed":
                passed = character.quest_state.get(condition["quest_key"], {}).get("completed", False)
            elif kind == "quest_state":
                state = character.quest_state.get(condition["quest_key"], {}).get("state", "not_started")
                passed = state == condition["state"]
            else:
                raise ValueError("unsupported quest condition")
            if not passed:
                return False
        return True

    def accept(self, character, quest_key, npc_key):
        quest = self.definition("quests", quest_key)
        npc = self.definition("npcs", npc_key)
        if quest.rules["giver_npc_key"] != npc_key or quest_key not in npc.rules.get("available_quests", []):
            raise ValueError("this NPC does not offer that quest")
        if quest_key in character.quest_state:
            return  # Reopening/retrying a conversation never resets old progress.
        if not self.conditions_met(character, quest.rules.get("start_conditions", [])):
            raise ValueError("quest requirements are not met")
        if any(o["type"] not in {"defeat_enemy", "inspect_landmark", "talk_to_npc", "cast_spell"} for o in quest.rules["objectives"]):
            raise ValueError("quest objective is not playable yet")
        character.quest_state[quest_key] = {
            "state": "accepted", "objectives": {o["key"]: 0 for o in quest.rules["objectives"]},
            "completed": False, "rewards_claimed": False,
        }

    def advance(self, character, event_type, target, context=None):
        """Apply a server-observed event once to each eligible active quest."""
        target_fields = {"defeat_enemy": "enemy_key", "inspect_landmark": "interaction_key", "talk_to_npc": "npc_key", "cast_spell": "spell_key"}
        context = context or {}
        if event_type not in target_fields:
            raise ValueError("unsupported quest event")
        for key, progress in character.quest_state.items():
            if progress.get("state") != "accepted" or progress.get("rewards_claimed"):
                continue
            quest = self.definition("quests", key)
            objectives = quest.rules["objectives"]
            for objective in objectives:
                done = progress["objectives"].get(objective["key"], 0)
                if done >= objective["quantity"]:
                    continue
                in_zone = objective.get("zone_key", character.current_zone_key) == character.current_zone_key
                cast_matches = event_type != "cast_spell" or (
                    context.get("enemy_key") == objective.get("enemy_key", context.get("enemy_key"))
                    and context.get("intent_power", -1) >= objective.get("intent_power_at_least", 0))
                if in_zone and cast_matches and objective["type"] == event_type and objective[target_fields[event_type]] == target:
                    progress["objectives"][objective["key"]] = min(objective["quantity"], done + 1)
                if quest.rules.get("ordered", False):
                    break  # A later objective cannot be pre-completed by a repeated request.
            if not all(progress["objectives"].get(o["key"], 0) >= o["quantity"] for o in objectives):
                continue
            for reward in quest.rules["rewards"]:
                if reward["type"] == "grant_experience":
                    character.experience += reward["amount"]
                elif reward["type"] == "grant_currency":
                    currency = reward["currency_key"]
                    character.wallet[currency] = character.wallet.get(currency, 0) + reward["amount"]
                elif reward["type"] == "grant_item":
                    item = reward["item_key"]
                    character.inventory[item] = character.inventory.get(item, 0) + reward["quantity"]
                elif reward["type"] == "learn_spell":
                    spell = self.definition("spells", reward["spell_key"]).key
                    if spell not in character.known_spells:
                        character.known_spells.append(spell)
                else:
                    raise ValueError("unsupported quest reward")
            progress.update(state="completed", completed=True, rewards_claimed=True)

    def _graph(self, npc_key):
        npc = self.definition("npcs", npc_key)
        return npc, self.definition("dialogue", npc.rules["dialogue_key"])

    def start_dialogue(self, character, npc_key):
        zone = self.definition("zones", character.current_zone_key)
        if npc_key not in zone.rules.get("npcs", []):
            raise ValueError("NPC is not in this region")
        npc, graph = self._graph(npc_key)
        node = graph.rules["start_node"]
        for entry in graph.rules.get("entry_nodes", []):
            if self.conditions_met(character, entry.get("conditions", [])):
                node = entry["node"]
                break
        character.dialogue_state = {"id": str(uuid4()), "npc_key": npc.key,
                                    "graph_version": graph.version, "node": node}
        return self.dialogue_view(character)

    def dialogue_view(self, character):
        cursor = character.dialogue_state
        if not cursor:
            return None
        npc, graph = self._graph(cursor["npc_key"])
        node = graph.rules["nodes"][cursor["node"]]
        return {"id": cursor["id"], "npc_key": npc.key, "speaker": npc.display.name,
                "node": cursor["node"], "text": node["text"],
                "options": [{"key": o["key"], "text": o["text"]} for o in node.get("options", [])
                            if self.conditions_met(character, o.get("conditions", []))]}

    def choose_dialogue(self, character, npc_key, conversation_id, option_key):
        cursor = character.dialogue_state
        npc, graph = self._graph(npc_key)
        if not cursor or cursor["id"] != conversation_id or cursor["npc_key"] != npc_key or cursor["graph_version"] != graph.version:
            raise ValueError("conversation changed; speak to the NPC again")
        node = graph.rules["nodes"][cursor["node"]]
        option = next((o for o in node.get("options", []) if o["key"] == option_key), None)
        if option is None or not self.conditions_met(character, option.get("conditions", [])):
            raise ValueError("dialogue choice is not available")
        for effect in option.get("effects", []):
            if effect["type"] != "offer_quest":
                raise ValueError("unsupported dialogue effect")
            self.accept(character, effect["quest_key"], npc.key)
        if option.get("next_node"):
            # Rotate the cursor token so a late duplicate cannot choose at a later node.
            character.dialogue_state = {**cursor, "id": str(uuid4()), "node": option["next_node"]}
        else:
            character.dialogue_state = {}
        return self.dialogue_view(character)

    def inspect(self, character, interaction_key):
        zone = self.definition("zones", character.current_zone_key)
        discovery = zone.rules.get("discoveries", {}).get(interaction_key)
        if discovery is None:
            raise ValueError("there is nothing to inspect here")
        self.advance(character, "inspect_landmark", interaction_key)
        return deepcopy(discovery)
