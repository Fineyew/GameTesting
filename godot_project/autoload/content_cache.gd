extends Node

signal manifest_loaded(entry_count: int)

var manifest := {}
var definitions := {}


func refresh_manifest() -> void:
    manifest = await ApiClient.get_json("/content/manifest")
    var entries: Array = manifest.get("entries", [])
    manifest_loaded.emit(entries.size())


func get_definition(content_type: String, key: String) -> Dictionary:
    var cache_key := "%s/%s" % [content_type, key]
    if definitions.has(cache_key):
        return definitions[cache_key]

    var definition := await ApiClient.get_json("/content/%s/%s" % [content_type, key])
    if not definition.is_empty():
        definitions[cache_key] = definition
    return definition


func clear() -> void:
    manifest.clear()
    definitions.clear()
