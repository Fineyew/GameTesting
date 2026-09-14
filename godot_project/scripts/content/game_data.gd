class_name GameData
extends RefCounted
static var definitions: Dictionary = {}

static func load_bundle() -> void:
    var parsed = JSON.parse_string(FileAccess.get_file_as_string("res://data/catalog.json"))
    if parsed is Dictionary:
        set_definitions(parsed.get("definitions", []))

static func set_definitions(items: Array) -> void:
    definitions.clear()
    for item in items:
        definitions[item.type + "/" + item.key] = item

static func definition(category: String, key: String) -> Dictionary:
    return definitions.get(category + "/" + key, {})

static func display_name(category: String, key: String) -> String:
    return definition(category, key).get("display", {}).get("name", key.replace("_", " ").capitalize())
