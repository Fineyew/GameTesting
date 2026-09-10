"""Deterministic Tidebeat rules. The catalog is an injected read port, never a database."""
from copy import deepcopy


class CombatEngine:
    def __init__(self, catalog):
        self.catalog = catalog

    def begin(self, enemy_key, vigor, prepared_spells):
        enemy = self.catalog.get_definition("enemies", enemy_key)
        intents = deepcopy(enemy.rules["intents"])
        return {"enemy_key": enemy_key, "enemy_name": enemy.display.name,
                "enemy_vigor": enemy.rules["stats"]["vigor"], "enemy_max_vigor": enemy.rules["stats"]["vigor"],
                "player_vigor": vigor, "player_max_vigor": 30, "focus": 3, "round": 1,
                "state": "active", "mark": 0, "intent_index": 0, "intents": intents, "intent": intents[0],
                "spells": {key: {"name": self.catalog.get_definition("spells", key).display.name,
                                  **deepcopy(self.catalog.get_definition("spells", key).rules)} for key in prepared_spells},
                "log": [f"{enemy.display.name} emerges from the mist."]}

    def resolve(self, original, action):
        state = deepcopy(original)
        if state["state"] != "active":
            raise ValueError("encounter already finished")
        guard = binding = 0
        if action == "brace":
            guard = 6
            state["log"].append("You brace: absorb 6 damage this beat.")
        elif action == "gather":
            state["focus"] = min(6, state["focus"] + 2)
            state["log"].append("You gather 2 Focus.")
        else:
            if action not in state["spells"]:
                raise ValueError("spell is not prepared")
            spell = state["spells"][action]
            cost = sum(c["amount"] for c in spell.get("costs", []))
            if cost > state["focus"]:
                raise ValueError("not enough Focus")
            state["focus"] -= cost
            state["log"].append(f"You cast {spell['name']}.")
            for effect in spell["effects"]:
                kind = effect["type"]
                amount = effect.get("amount", effect.get("power", 0))
                if kind == "deal_damage":
                    state["enemy_vigor"] = max(0, state["enemy_vigor"] - amount - state["mark"])
                    state["mark"] = 0
                elif kind == "restore_vigor":
                    state["player_vigor"] = min(state["player_max_vigor"], state["player_vigor"] + amount)
                elif kind == "bind":
                    binding += amount
                elif kind == "guard":
                    guard += amount
                elif kind == "mark":
                    state["mark"] = min(12, state["mark"] + amount)
                else:
                    raise ValueError("unsupported combat effect")
        if state["enemy_vigor"] == 0:
            state["state"] = "victory"
            state["log"].append("The lurker retreats. Rewards saved.")
        else:
            incoming = max(0, state["intent"]["power"] - guard - binding)
            state["player_vigor"] = max(0, state["player_vigor"] - incoming)
            state["log"].append(f"{state['intent']['name']}: {incoming} damage.")
            if state["player_vigor"] == 0 or state["round"] >= 50:
                state["state"] = "defeat"
                state["log"].append("The Lantern Well calls you home. Vigor restored.")
        state["round"] += 1
        state["focus"] = min(6, state["focus"] + 1)
        state["intent_index"] = (state["intent_index"] + 1) % len(state["intents"])
        state["intent"] = state["intents"][state["intent_index"]]
        state["log"] = state["log"][-12:]
        return state
