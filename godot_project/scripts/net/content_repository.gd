class_name ContentRepository
extends RefCounted

signal manifest_loaded(entry_count: int)

var manifest := {}
var definitions := {}
var _api_client: Node


func _init(api_client: Node) -> void:
    _api_client = api_client


func refresh_manifest() -> Dictionary:
    manifest = await _api_client.get_json("/content/manifest")
    var entries: Array = manifest.get("entries", [])
    manifest_loaded.emit(entries.size())
    return manifest


func get_definition(content_type: String, key: String) -> Dictionary:
    var cache_key := "%s/%s" % [content_type, key]
    if definitions.has(cache_key):
        return definitions[cache_key]

    var definition: Dictionary = await _api_client.get_json("/content/%s/%s" % [content_type, key])
    if not definition.is_empty():
        definitions[cache_key] = definition
    return definition


func clear() -> void:
    manifest.clear()
    definitions.clear()
