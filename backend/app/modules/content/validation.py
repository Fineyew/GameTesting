import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_CONTENT_CATEGORIES = {
    "achievements",
    "crafting",
    "dialogue",
    "dungeons",
    "enemies",
    "equipment",
    "gathering",
    "items",
    "loot_tables",
    "mounts",
    "npcs",
    "quests",
    "shops",
    "spells",
    "zones",
}

KNOWN_EFFECT_TYPES = {
    "deal_damage",
    "bind",
    "mark",
    "guard",
    "grant_currency",
    "grant_experience",
    "grant_item",
    "learn_spell",
    "offer_quest",
    "restore_vigor",
}

KNOWN_CONDITION_TYPES = {
    "character_level_at_least",
    "quest_completed",
    "quest_state",
}

KNOWN_OBJECTIVE_TYPES = {
    "collect_item",
    "defeat_enemy",
    "inspect_landmark",
    "talk_to_npc",
    "cast_spell",
}


@dataclass(frozen=True)
class LoadedContent:
    path: Path
    payload: dict[str, Any]


@dataclass
class ContentValidationReport:
    definitions: dict[tuple[str, str], LoadedContent] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_content_tree(root: Path) -> ContentValidationReport:
    report = ContentValidationReport()
    _validate_required_categories(root, report)
    _load_definitions(root, report)
    if report.errors:
        return report
    _validate_references(report)
    return report


def _validate_required_categories(root: Path, report: ContentValidationReport) -> None:
    for category in sorted(REQUIRED_CONTENT_CATEGORIES):
        if not (root / category).is_dir():
            report.errors.append(f"Missing required content category: {category}")


def _load_definitions(root: Path, report: ContentValidationReport) -> None:
    for path in sorted(root.glob("*/*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.errors.append(f"{path}: invalid JSON: {exc}")
            continue

        if not isinstance(payload, dict):
            report.errors.append(f"{path}: definition must be an object")
            continue
        _validate_base_shape(path, payload, report)
        content_type = payload.get("type")
        key = payload.get("key")
        version = payload.get("version")
        if not isinstance(content_type, str) or not isinstance(key, str) or not isinstance(version, int):
            continue

        identity = (content_type, key)
        existing = report.definitions.get(identity)
        if existing is not None:
            report.errors.append(f"{path}: duplicate content key also defined at {existing.path}")
            continue

        report.definitions[identity] = LoadedContent(path=path, payload=payload)


def _validate_base_shape(path: Path, payload: dict[str, Any], report: ContentValidationReport) -> None:
    expected_type = path.parent.name
    expected_key = path.stem

    if payload.get("type") != expected_type:
        report.errors.append(f"{path}: type must match directory '{expected_type}'")
    if payload.get("key") != expected_key:
        report.errors.append(f"{path}: key must match filename '{expected_key}'")
    if payload.get("schema_version") != 1:
        report.errors.append(f"{path}: schema_version must be 1")
    if not isinstance(payload.get("version"), int) or payload.get("version", 0) < 1:
        report.errors.append(f"{path}: version must be an integer >= 1")

    display = payload.get("display")
    if not isinstance(display, dict) or not display.get("name"):
        report.errors.append(f"{path}: display.name is required")

    if not isinstance(payload.get("rules", {}), dict):
        report.errors.append(f"{path}: rules must be an object")
    if not isinstance(payload.get("assets", {}), dict):
        report.errors.append(f"{path}: assets must be an object")
    if not isinstance(payload.get("tags", []), list):
        report.errors.append(f"{path}: tags must be a list")


def _validate_references(report: ContentValidationReport) -> None:
    for loaded in report.definitions.values():
        payload = loaded.payload
        rules = payload.get("rules", {})
        path = loaded.path
        if not _validate_rule_lists(path, rules, report):
            continue
        _validate_handlers(path, rules, report)
        _validate_common_references(path, rules, report)
        _validate_type_specific_references(path, payload.get("type"), rules, report)


def _validate_handlers(path: Path, rules: dict[str, Any], report: ContentValidationReport) -> None:
    for field in ("conditions", "start_conditions", "unlock_conditions"):
        for condition in _walk_dicts_by_key(rules, field):
            condition_type = condition.get("type")
            if condition_type not in KNOWN_CONDITION_TYPES:
                report.errors.append(f"{path}: unknown condition type '{condition_type}'")
            elif condition_type == "character_level_at_least" and not _bounded_integer(condition.get("value"), 1, 1000):
                report.errors.append(f"{path}: invalid minimum level")
            elif condition_type == "quest_state" and condition.get("state") not in {"not_started", "accepted", "completed"}:
                report.errors.append(f"{path}: invalid quest state condition")
            if condition_type in {"quest_completed", "quest_state"} and not isinstance(condition.get("quest_key"), str):
                report.errors.append(f"{path}: quest condition requires quest_key")

    for field in ("effects", "rewards", "use_effects"):
        for effect in _walk_dicts_by_key(rules, field):
            effect_type = effect.get("type")
            if effect_type not in KNOWN_EFFECT_TYPES:
                report.errors.append(f"{path}: unknown effect type '{effect_type}'")

    for objective in rules.get("objectives", []):
        objective_type = objective.get("type")
        if objective_type not in KNOWN_OBJECTIVE_TYPES:
            report.errors.append(f"{path}: unknown objective type '{objective_type}'")


def _validate_common_references(path: Path, rules: dict[str, Any], report: ContentValidationReport) -> None:
    reference_fields = {
        "achievement_key": "achievements",
        "dialogue_key": "dialogue",
        "dungeon_key": "dungeons",
        "enemy_key": "enemies",
        "loot_table_key": "loot_tables",
        "mount_key": "mounts",
        "npc_key": "npcs",
        "giver_npc_key": "npcs",
        "quest_key": "quests",
        "recipe_key": "crafting",
        "shop_key": "shops",
        "spell_key": "spells",
        "zone_key": "zones",
    }

    for field, content_type in reference_fields.items():
        for key in _walk_values_by_key(rules, field):
            _require_reference(path, content_type, key, report)

    for item_key in _walk_values_by_key(rules, "item_key"):
        if not _has_reference(report, "items", item_key) and not _has_reference(report, "equipment", item_key):
            report.errors.append(f"{path}: missing item/equipment reference '{item_key}'")


def _validate_type_specific_references(
    path: Path,
    content_type: str,
    rules: dict[str, Any],
    report: ContentValidationReport,
) -> None:
    if content_type == "quests":
        _validate_quest(path, rules, report)
    if content_type == "dialogue":
        _validate_dialogue(path, rules, report)
    if content_type == "items":
        if not _bounded_integer(rules.get("stack_limit"), 1, 10000):
            report.errors.append(f"{path}: invalid item stack limit")
        if ("equipment", path.stem) in report.definitions:
            report.errors.append(f"{path}: item and equipment keys must not collide")
    if content_type == "equipment":
        if rules.get("slot") != "chest" or rules.get("stack_limit") != 1 or type(rules.get("stack_limit")) is not int:
            report.errors.append(f"{path}: equipment requires chest slot and stack_limit 1")
        if not _bounded_integer(rules.get("required_level"), 1, 1000):
            report.errors.append(f"{path}: invalid equipment level")
        modifiers = rules.get("modifiers")
        if not isinstance(modifiers, list) or len(modifiers) != 1 or any(
            not isinstance(m, dict) or set(m) != {"stat", "operation", "value"} or m.get("stat") != "guard" or
            m.get("operation") != "add" or not _bounded_integer(m.get("value"), 0, 3) for m in modifiers
        ):
            report.errors.append(f"{path}: equipment supports one additive guard modifier (0–3)")
    if content_type == "shops":
        _validate_shop(path, rules, report)
    if content_type == "spells":
        for cost in rules.get("costs", []):
            if cost.get("resource") != "focus" or type(cost.get("amount")) is not int or not 0 <= cost["amount"] <= 6:
                report.errors.append(f"{path}: invalid Focus cost")
        for effect in rules.get("effects", []):
            if effect.get("type") not in {"deal_damage", "restore_vigor", "bind", "mark", "guard"}:
                report.errors.append(f"{path}: unsupported combat effect")
            amount = effect.get("amount", effect.get("power"))
            if type(amount) is not int or not 0 <= amount <= 10000:
                report.errors.append(f"{path}: invalid effect amount")
    if content_type == "enemies":
        intents = rules.get("intents", [])
        if not 1 <= len(intents) <= 12 or any(type(i.get("power")) is not int or not 0 <= i["power"] <= 30 for i in intents):
            report.errors.append(f"{path}: invalid enemy intents")
    if content_type == "zones":
        for key, discovery in rules.get("discoveries", {}).items():
            if key not in rules.get("world", {}).get("interactions", {}) or not isinstance(discovery, dict) or not discovery.get("text") or not discovery.get("title"):
                report.errors.append(f"{path}: invalid discovery '{key}'")
        for node_key in rules.get("gathering_nodes", []):
            _require_reference(path, "gathering", node_key, report)
        for npc_key in rules.get("npcs", []):
            _require_reference(path, "npcs", npc_key, report)
        for enemy_key in rules.get("encounters", []):
            _require_reference(path, "enemies", enemy_key, report)

    if content_type == "npcs":
        for quest_key in rules.get("available_quests", []):
            _require_reference(path, "quests", quest_key, report)
        dialogue = report.definitions.get(("dialogue", rules.get("dialogue_key")))
        if dialogue:
            for effect in _walk_dicts_by_key(dialogue.payload["rules"], "effects"):
                if effect.get("type") == "offer_quest" and effect.get("quest_key") not in rules.get("available_quests", []):
                    report.errors.append(f"{path}: dialogue offers a quest not assigned to this NPC")

    if content_type == "dungeons":
        for room in rules.get("rooms", []):
            for enemy_key in room.get("enemy_keys", []):
                _require_reference(path, "enemies", enemy_key, report)


def _bounded_integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


def _validate_shop(path, rules, report):
    npc = report.definitions.get(("npcs", rules.get("npc_key"))) if isinstance(rules.get("npc_key"), str) else None
    zone = report.definitions.get(("zones", rules.get("zone_key"))) if isinstance(rules.get("zone_key"), str) else None
    if not npc or npc.payload["rules"].get("shop_key") != path.stem or not zone or rules.get("npc_key") not in zone.payload["rules"].get("world", {}).get("interactions", {}):
        report.errors.append(f"{path}: shop requires a matching NPC and world interaction")
    listings = rules.get("listings")
    if not isinstance(listings, list) or not 1 <= len(listings) <= 16 or any(not isinstance(row, dict) for row in listings):
        report.errors.append(f"{path}: shop requires 1–16 listing objects")
        return
    keys = [row.get("key") for row in listings]
    if any(not isinstance(k, str) or not 1 <= len(k) <= 64 for k in keys) or len(set(str(k) for k in keys)) != len(keys):
        report.errors.append(f"{path}: duplicate or invalid listing keys")
    for row in listings:
        if not _bounded_integer(row.get("quantity"), 1, 100) or type(row.get("available")) is not bool:
            report.errors.append(f"{path}: invalid listing quantity/availability")
        if row.get("available") is False and (not isinstance(row.get("unavailable_reason"), str) or not row["unavailable_reason"].strip()):
            report.errors.append(f"{path}: unavailable listing requires a reason")
        price = row.get("price")
        if not isinstance(price, list) or len(price) != 1 or any(
            not isinstance(p, dict) or set(p) != {"currency_key", "amount"} or p.get("currency_key") != "shell_chits" or
            not _bounded_integer(p.get("amount"), 1, 10000) for p in price
        ):
            report.errors.append(f"{path}: price requires one positive shell_chits amount (1–10000)")


def _validate_rule_lists(path, value, report):
    valid = True
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"conditions", "start_conditions", "unlock_conditions", "effects", "rewards", "use_effects", "objectives", "entry_nodes"}:
                if not isinstance(child, list) or any(not isinstance(entry, dict) for entry in child):
                    report.errors.append(f"{path}: {key} must be a list of objects")
                    valid = False
            valid = _validate_rule_lists(path, child, report) and valid
    elif isinstance(value, list):
        for child in value:
            valid = _validate_rule_lists(path, child, report) and valid
    return valid


def _validate_quest(path, rules, report):
    _require_reference(path, "npcs", rules.get("giver_npc_key"), report)
    objectives = rules.get("objectives")
    if not isinstance(objectives, list) or not 1 <= len(objectives) <= 16 or any(not isinstance(o, dict) for o in objectives):
        report.errors.append(f"{path}: quests need 1–16 objective objects")
        return
    keys = [o.get("key") for o in objectives]
    if any(not isinstance(k, str) or not k for k in keys) or len(set(str(k) for k in keys)) != len(keys):
        report.errors.append(f"{path}: objective keys must be unique nonempty strings")
    for objective in objectives:
        if not _bounded_integer(objective.get("quantity"), 1, 1000):
            report.errors.append(f"{path}: invalid objective quantity")
        kind = objective.get("type")
        field = {"defeat_enemy": "enemy_key", "collect_item": "item_key", "talk_to_npc": "npc_key", "inspect_landmark": "interaction_key", "cast_spell": "spell_key"}.get(kind)
        if field and not isinstance(objective.get(field), str):
            report.errors.append(f"{path}: objective requires {field}")
        if kind in {"inspect_landmark", "talk_to_npc"} and objective.get("quantity") != 1:
            report.errors.append(f"{path}: discovery/dialogue objectives must have quantity1")
        if kind == "inspect_landmark":
            zone = report.definitions.get(("zones", objective.get("zone_key")))
            if not zone or objective.get("interaction_key") not in zone.payload["rules"].get("discoveries", {}):
                report.errors.append(f"{path}: unknown inspectable landmark")
        if "intent_power_at_least" in objective and (kind != "cast_spell" or not _bounded_integer(objective["intent_power_at_least"], 0, 30)):
            report.errors.append(f"{path}: invalid cast intent threshold")
    if type(rules.get("ordered", False)) is not bool:
        report.errors.append(f"{path}: ordered must be boolean")
    rewards = rules.get("rewards")
    if not isinstance(rewards, list) or len(rewards) > 16 or any(not isinstance(r, dict) for r in rewards):
        report.errors.append(f"{path}: invalid quest rewards")
        return
    for reward in rewards:
        kind = reward.get("type")
        if kind not in {"grant_experience", "grant_currency", "grant_item", "learn_spell"}:
            report.errors.append(f"{path}: unsupported quest reward")
        if kind == "learn_spell":
            if set(reward) != {"type", "spell_key"}:
                report.errors.append(f"{path}: learn_spell requires only a spell_key; no quantities or amounts")
            _require_reference(path, "spells", reward.get("spell_key"), report)
            continue
        if not _bounded_integer(reward.get("quantity" if kind == "grant_item" else "amount"), 1, 10000):
            report.errors.append(f"{path}: invalid quest reward amount")
        if kind == "grant_currency" and (not isinstance(reward.get("currency_key"), str) or not 1 <= len(reward["currency_key"]) <= 64):
            report.errors.append(f"{path}: invalid reward currency")
        if kind == "grant_item" and not isinstance(reward.get("item_key"), str):
            report.errors.append(f"{path}: item reward requires item_key")


def _validate_dialogue(path, rules, report):
    nodes = rules.get("nodes")
    if not isinstance(nodes, dict) or not 1 <= len(nodes) <= 32 or rules.get("start_node") not in nodes:
        report.errors.append(f"{path}: dialogue requires valid nodes/start_node")
        return
    for entry in rules.get("entry_nodes", []):
        if not isinstance(entry, dict) or entry.get("node") not in nodes:
            report.errors.append(f"{path}: invalid dialogue entry node")
    for node in nodes.values():
        if not isinstance(node, dict) or not isinstance(node.get("text"), str) or not node["text"].strip():
            report.errors.append(f"{path}: dialogue node requires text")
            continue
        options = node.get("options", [])
        if not isinstance(options, list) or len(options) > 8 or any(not isinstance(o, dict) for o in options):
            report.errors.append(f"{path}: invalid dialogue options")
            continue
        keys = [o.get("key") for o in options]
        if any(not isinstance(k, str) or not k for k in keys) or len(set(str(k) for k in keys)) != len(keys):
            report.errors.append(f"{path}: dialogue choice keys must be unique")
        for option in options:
            if not isinstance(option.get("text"), str) or not option["text"].strip():
                report.errors.append(f"{path}: dialogue choice requires text")
            if option.get("next_node") is not None and option["next_node"] not in nodes:
                report.errors.append(f"{path}: missing next_node")
            for effect in option.get("effects", []):
                if effect.get("type") != "offer_quest":
                    report.errors.append(f"{path}: dialogue may offer quests, not grant rewards directly")


def _require_reference(
    path: Path,
    content_type: str,
    key: Any,
    report: ContentValidationReport,
) -> None:
    if not isinstance(key, str) or not _has_reference(report, content_type, key):
        report.errors.append(f"{path}: missing {content_type} reference '{key}'")


def _has_reference(report: ContentValidationReport, content_type: str, key: Any) -> bool:
    return isinstance(key, str) and (content_type, key) in report.definitions


def _walk_dicts_by_key(value: Any, key: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key and isinstance(current_value, list):
                found.extend(item for item in current_value if isinstance(item, dict))
            else:
                found.extend(_walk_dicts_by_key(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_dicts_by_key(item, key))
    return found


def _walk_values_by_key(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key:
                found.append(current_value)
            else:
                found.extend(_walk_values_by_key(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(_walk_values_by_key(item, key))
    return found
