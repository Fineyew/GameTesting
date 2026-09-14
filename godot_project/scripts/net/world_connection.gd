class_name WorldConnection
extends Node
signal snapshot_received(frame: Dictionary)
signal state_changed(message: String)
var socket: WebSocketPeer
var character_id := ""
var axis := Vector2.ZERO
var running := false
var connected := false
var authenticated := false
var sequence := 0
var send_elapsed := 0.0
var reconnect_in := 0.0
var backoff := 1.0
var attempt_elapsed := 0.0
var geometry_digest := ""
var geometry_revision := 2

func start(identity: String) -> void:
    stop()
    character_id = identity
    var geometry = GameData.definition("zones","dawnreef_atoll").rules.world
    geometry_digest = TerrainSurface.digest(geometry)
    geometry_revision = geometry.get("geometry_revision",1)
    running = true
    backoff = 1
    _connect()

func _connect() -> void:
    connected = false
    authenticated = false
    attempt_elapsed = 0
    sequence = 0
    socket = WebSocketPeer.new()
    socket.inbound_buffer_size = 65536
    socket.outbound_buffer_size = 8192
    var url = ApiClient.base_url.replace("https://", "wss://").replace("http://", "ws://") + "/world/socket"
    socket.connect_to_url(url)
    state_changed.emit("Connecting to Dawnreef…")

func _process(delta: float) -> void:
    if not running:
        return
    if reconnect_in > 0:
        reconnect_in -= delta
        if reconnect_in <= 0:
            _connect()
        return
    attempt_elapsed += delta
    socket.poll()
    var state = socket.get_ready_state()
    if state == WebSocketPeer.STATE_OPEN:
        if not authenticated:
            socket.send_text(JSON.stringify({"type":"auth", "protocol":2,"geometry_digest":geometry_digest,"geometry_revision":geometry_revision, "token":ApiClient.access_token,"character_id":character_id}))
            authenticated = true
        while socket.get_available_packet_count() > 0:
            var packet = JSON.parse_string(socket.get_packet().get_string_from_utf8())
            if packet is Dictionary:
                if packet.get("protocol") != 2 or packet.get("geometry_digest") != geometry_digest or packet.get("geometry_revision") != geometry_revision:
                    running = false
                    connected = false
                    socket.close()
                    state_changed.emit("World update required · return to sign in")
                    return
                if packet.get("type") == "welcome":
                    connected = true
                    backoff = 1
                    state_changed.emit("Connected · Dawnreef")
                elif packet.get("type") == "snapshot":
                    snapshot_received.emit(packet)
        send_elapsed += delta
        if connected and send_elapsed >= .1:
            send_elapsed = 0
            sequence += 1
            socket.send_text(JSON.stringify({"type":"move", "seq":sequence,"axis":[axis.x,axis.y]}))
    elif state == WebSocketPeer.STATE_CLOSED or attempt_elapsed > 12 and not connected:
        var code = socket.get_close_code()
        connected = false
        if code == 4004:
            running = false
            state_changed.emit("World update required · install matching game build")
        elif code == 4003 or code == 4001:
            running = false
            state_changed.emit("Session ended · return to sign in")
        else:
            socket.close()
            reconnect_in = backoff + randf()*.3
            backoff = minf(12,backoff*2)
            state_changed.emit("Connection lost · reconnecting…")

func say(phrase: String) -> void:
    if connected:
        socket.send_text(JSON.stringify({"type":"say", "phrase":phrase}))

func stop() -> void:
    running = false
    connected = false
    reconnect_in = 0
    if socket:
        socket.close()
