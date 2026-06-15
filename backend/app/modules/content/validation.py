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
    "grant_currency",
    "grant_experience",
    "grant_item",
    "offer_quest",
    "restore_vigor",
}

KNOWN_CONDITION_TYPES = {
    "character_level_at_least",
    "quest_completed",
}

KNOWN_OBJECTIVE_TYPES = {
    "collect_item",
    "defeat_enemy",
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

        _validate_handlers(path, rules, report)
        _validate_common_references(path, rules, report)
        _validate_type_specific_references(path, payload.get("type"), rules, report)


def _validate_handlers(path: Path, rules: dict[str, Any], report: ContentValidationReport) -> None:
    for field in ("conditions", "start_conditions", "unlock_conditions"):
        for condition in _walk_dicts_by_key(rules, field):
            condition_type = condition.get("type")
            if condition_type not in KNOWN_CONDITION_TYPES:
                report.errors.append(f"{path}: unknown condition type '{condition_type}'")

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
    if content_type == "zones":
        for node_key in rules.get("gathering_nodes", []):
            _require_reference(path, "gathering", node_key, report)
        for npc_key in rules.get("npcs", []):
            _require_reference(path, "npcs", npc_key, report)
        for enemy_key in rules.get("encounters", []):
            _require_reference(path, "enemies", enemy_key, report)

    if content_type == "npcs":
        for quest_key in rules.get("available_quests", []):
            _require_reference(path, "quests", quest_key, report)

    if content_type == "dungeons":
        for room in rules.get("rooms", []):
            for enemy_key in room.get("enemy_keys", []):
                _require_reference(path, "enemies", enemy_key, report)


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
