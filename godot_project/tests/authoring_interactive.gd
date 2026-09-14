extends SceneTree

func _init() -> void:
    call_deferred("run")

func run() -> void:
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    app.server_url = OS.get_environment("VT_TEST_API_URL")
    app.status_label.text = "Isolated authoring preview · temporary accounts and saves."
