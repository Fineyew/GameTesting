extends Node

signal request_failed(endpoint: String, status_code: int, message: String)

var base_url := "http://127.0.0.1/api/v1"
var access_token := ""


func set_session(new_base_url: String, token: String) -> void:
    base_url = new_base_url.trim_suffix("/")
    access_token = token


func get_json(endpoint: String) -> Dictionary:
    var request := HTTPRequest.new()
    add_child(request)

    var headers := _auth_headers()
    var err := request.request("%s%s" % [base_url, endpoint], headers, HTTPClient.METHOD_GET)
    if err != OK:
        request.queue_free()
        request_failed.emit(endpoint, 0, "Unable to start request")
        return {}

    var result: Array = await request.request_completed
    request.queue_free()
    return _parse_response(endpoint, result)


func post_json(endpoint: String, payload: Dictionary, idempotency_key := "") -> Dictionary:
    var request := HTTPRequest.new()
    add_child(request)

    var headers := _auth_headers()
    headers.append("Content-Type: application/json")
    if not idempotency_key.is_empty():
        headers.append("Idempotency-Key: %s" % idempotency_key)

    var body := JSON.stringify(payload)
    var err := request.request("%s%s" % [base_url, endpoint], headers, HTTPClient.METHOD_POST, body)
    if err != OK:
        request.queue_free()
        request_failed.emit(endpoint, 0, "Unable to start request")
        return {}

    var result: Array = await request.request_completed
    request.queue_free()
    return _parse_response(endpoint, result)


func _auth_headers() -> PackedStringArray:
    var headers := PackedStringArray()
    if not access_token.is_empty():
        headers.append("Authorization: Bearer %s" % access_token)
    return headers


func _parse_response(endpoint: String, result: Array) -> Dictionary:
    var status_code: int = result[1]
    var body: PackedByteArray = result[3]
    var text := body.get_string_from_utf8()
    var parsed = JSON.parse_string(text) if not text.is_empty() else {}

    if status_code < 200 or status_code >= 300:
        request_failed.emit(endpoint, status_code, text)
        return {}

    if typeof(parsed) == TYPE_DICTIONARY:
        return parsed
    return {"data": parsed}
