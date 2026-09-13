extends Node
## Local presentation only. No combat decisions, rewards or network messages.
signal caption_requested(words: String)
const DEFAULTS = {"Master":.85,"Music":.65,"Ambience":.65,"Movement":.65,"Spells":.75,"Creatures":.65,"UI":.6}
const LOOPS = ["res://audio/dawnreef_theme.ogg","res://audio/tidebeat_theme.ogg","res://audio/reef_wind.ogg"]
const CUES = {
    "creature_shell":["res://audio/creature_shell.wav","Creatures","Shell plates click together"],
    "creature_ray":["res://audio/creature_ray.wav","Creatures","The ray draws a quiet breath"],
    "root_cast":["res://audio/root_cast.wav","Spells","Reed-roots tighten"],
    "tide_cast":["res://audio/tide_cast.wav","Spells","A tide seam opens"],
    "ui":["res://audio/ui.wav","UI","Soft button chime"],
    "footstep":["res://audio/footstep.wav","Movement","Footsteps"],
    "cast":["res://audio/cast.wav","Spells","A lens gathers light"],
    "impact":["res://audio/impact.wav","Spells","A spell strikes"],
    "mend":["res://audio/mend.wav","Spells","A warm seam closes"],
    "guard":["res://audio/guard.wav","Spells","A protective weave settles"],
    "creature":["res://audio/creature.wav","Creatures","The fog-thorn lurker stirs"],
    "discovery":["res://audio/discovery.wav","UI","A clear discovery chime"]}
const VOICE_LIMIT = 8
var levels: Dictionary = DEFAULTS.duplicate()
var reduced := false
var captions := false
var world_active := false
var combat_active := false
var ducked := false
var backgrounded := false
var world_gain := 0.0
var combat_mix := 0.0
var duck_gain := 1.0
var loops: Array[AudioStreamPlayer] = []
var voices: Array[AudioStreamPlayer] = []
var cue_streams: Dictionary = {}
var save_timer: Timer
var cooldowns: Dictionary = {}
var settings_path := "user://settings.cfg"
var foot_variant := 0
var last_caption := -2000
var debug_first_step := false
var closing := false

func _ready() -> void:
    if Engine.is_editor_hint():
        return # A fresh editor imports assets after constructing autoloads.
    process_mode = Node.PROCESS_MODE_ALWAYS
    get_tree().auto_accept_quit = false
    for bus in DEFAULTS:
        if AudioServer.get_bus_index(bus) < 0:
            AudioServer.add_bus()
            var index = AudioServer.bus_count-1
            AudioServer.set_bus_name(index,bus)
            AudioServer.set_bus_send(index,"Master")
    var limiter = AudioEffectHardLimiter.new()
    limiter.ceiling_db = -1.0
    AudioServer.add_bus_effect(0,limiter)
    save_timer = Timer.new()
    save_timer.one_shot = true
    save_timer.wait_time = .25
    save_timer.timeout.connect(save_settings)
    add_child(save_timer)
    for key in CUES:
        cue_streams[key] = load(CUES[key][0])
    for index in LOOPS.size():
        var stream = AudioStreamPlayer.new()
        stream.stream = load(LOOPS[index])
        stream.stream.loop = true
        stream.bus = "Ambience" if index == 2 else "Music"
        stream.volume_linear = 0
        add_child(stream)
        loops.append(stream)
    for index in VOICE_LIMIT:
        var voice = AudioStreamPlayer.new()
        add_child(voice)
        voices.append(voice)
    load_settings()
    if OS.is_debug_build():
        print("VT_AUDIO_READY")

func load_settings() -> void:
    var config = ConfigFile.new()
    config.load(settings_path)
    for bus in DEFAULTS:
        var saved = config.get_value("audio",bus,DEFAULTS[bus])
        levels[bus] = clampf(float(saved),0,1) if (saved is float or saved is int) and is_finite(float(saved)) else DEFAULTS[bus]
    reduced = config.get_value("audio","reduced",false) == true
    captions = config.get_value("audio","captions",false) == true
    apply_levels()

func save_settings() -> void:
    var config = ConfigFile.new()
    config.load(settings_path)
    for bus in levels:
        config.set_value("audio",bus,levels[bus])
    config.set_value("audio","reduced",reduced)
    config.set_value("audio","captions",captions)
    config.save(settings_path)

func set_volume(bus: String, value: float) -> void:
    if not levels.has(bus) or not is_finite(value):
        return
    levels[bus] = clampf(value,0,1)
    apply_levels()
    save_timer.start()

func set_reduced(value: bool) -> void:
    reduced = value
    apply_levels()
    save_timer.start()

func set_captions(value: bool) -> void:
    captions = value
    if not value:
        caption_requested.emit("")
    save_timer.start()

func apply_levels() -> void:
    for bus in levels:
        var index = AudioServer.get_bus_index(bus)
        var gain = levels[bus]*(.55 if reduced and bus in ["Spells","Creatures"] else 1.0)
        AudioServer.set_bus_volume_linear(index,gain)
        AudioServer.set_bus_mute(index,gain <= 0)

func set_world(value: bool) -> void:
    world_active = value
    if value:
        for stream in loops:
            if not stream.playing:
                stream.play()
            stream.stream_paused = backgrounded
    else:
        combat_active = false
        ducked = false
        for voice in voices:
            voice.stop()

func set_combat(value: bool) -> void:
    combat_active = world_active and value

func _process(delta: float) -> void:
    if loops.is_empty() or backgrounded:
        return
    var fade = 1.0-exp(-4.0*delta)
    world_gain = lerpf(world_gain,1.0 if world_active else 0.0,fade)
    combat_mix = lerpf(combat_mix,1.0 if combat_active else 0.0,fade)
    duck_gain = lerpf(duck_gain,.55 if ducked else 1.0,fade)
    loops[0].volume_linear = world_gain*duck_gain*sqrt(maxf(0,1-combat_mix))
    loops[1].volume_linear = world_gain*duck_gain*sqrt(maxf(0,combat_mix))
    loops[2].volume_linear = world_gain*duck_gain*(1.0-combat_mix*.3)
    if not world_active and world_gain < .001:
        for stream in loops:
            stream.stop()

func cue(key: String) -> bool:
    if backgrounded or not CUES.has(key) or (not world_active and CUES[key][1] != "UI"):
        return false
    var now = Time.get_ticks_msec()
    var interval = 140 if key == "footstep" else (600 if key.begins_with("creature") else 45)
    if now-int(cooldowns.get(key,-1000)) < interval:
        return false
    var available: AudioStreamPlayer
    for voice in voices:
        if not voice.playing:
            available = voice
            break
    if available == null:
        return false
    cooldowns[key] = now
    available.stream = cue_streams[key]
    available.bus = CUES[key][1]
    available.pitch_scale = (1.03 if foot_variant%2 else .97) if key == "footstep" else 1.0
    available.volume_linear = .65 if key == "footstep" else .8
    available.play()
    if key == "footstep":
        foot_variant += 1
        if OS.is_debug_build() and not debug_first_step:
            debug_first_step = true
            print("VT_AUDIO_FOOTSTEP")
    if captions and now-last_caption > 750 and key != "ui":
        caption_requested.emit(CUES[key][2])
        last_caption = now
    return true

func set_backgrounded(value: bool) -> void:
    backgrounded = value
    if value and is_instance_valid(save_timer) and not save_timer.is_stopped():
        save_settings()
        save_timer.stop()
    for stream in loops:
        stream.stream_paused = value
    for voice in voices:
        voice.stop() # Never replay an interrupted cue on return.
    if OS.is_debug_build():
        print("VT_AUDIO_PAUSED" if value else "VT_AUDIO_RESUMED")

func _notification(what: int) -> void:
    if Engine.is_editor_hint():
        return
    if what == NOTIFICATION_WM_CLOSE_REQUEST and not closing:
        closing = true
        close_application()
    elif what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
        set_backgrounded(true)
    elif what == NOTIFICATION_APPLICATION_RESUMED or what == NOTIFICATION_APPLICATION_FOCUS_IN:
        set_backgrounded(false)

func close_application() -> void:
    await shutdown()
    get_tree().quit.call_deferred()

func shutdown() -> void:
    set_world(false)
    world_gain = 0
    for stream in loops+voices:
        stream.stream_paused = false
        stream.stop()
        stream.stream = null
        stream.queue_free()
    loops.clear()
    voices.clear()
    cue_streams.clear()
    if not save_timer.is_stopped():
        save_settings()
        save_timer.stop()
    # Release player ownership before allowing the mixer to retire stopped playback.
    await get_tree().process_frame
    await get_tree().create_timer(.12,true,false,true).timeout

func _exit_tree() -> void:
    for stream in loops+voices:
        stream.stream_paused = false
        stream.stop()
        stream.stream = null
    cue_streams.clear()
    if is_instance_valid(save_timer) and not save_timer.is_stopped():
        save_settings()
