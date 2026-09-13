extends SceneTree
func _init() -> void:
    call_deferred("run")

func run() -> void:
    var sound = root.get_node("Soundscape")
    var config_path: String = sound.settings_path
    sound.settings_path = "user://audio-check.cfg"
    var fixture = ConfigFile.new()
    fixture.set_value("graphics","fps",60)
    fixture.set_value("network","server","https://example.invalid/api/v1")
    fixture.save(sound.settings_path)
    sound.load_settings()
    for bus in sound.DEFAULTS:
        assert(AudioServer.get_bus_index(bus) >= 0)
    assert(sound.loops.size() == 3 and sound.voices.size() == 8 and sound.cue_streams.size() == 8)
    for stream in sound.loops:
        assert(stream.stream.loop and stream.stream.get_length() >= 15)
    sound.set_world(true)
    for stream in sound.loops:
        stream.seek(stream.stream.get_length()-.04)
    await create_timer(.16).timeout
    assert(sound.loops.all(func(stream): return stream.playing and stream.get_playback_position() < .4),"Real mixer playback must wrap each loop")
    sound.set_process(false)
    for frame in 60:
        sound._process(1.0/30)
    assert(sound.loops[0].volume_linear > .99 and sound.loops[1].volume_linear == 0)
    sound.set_combat(true)
    for frame in 60:
        sound._process(1.0/30)
    assert(sound.loops[1].volume_linear > .99 and sound.loops[0].volume_linear < .03)
    sound.ducked = true
    for frame in 60:
        sound._process(1.0/30)
    assert(sound.loops[1].volume_linear < .56)
    sound.set_volume("Music",.3)
    sound.set_volume("Master",0)
    assert(AudioServer.is_bus_mute(0))
    sound.set_volume("Master",.8)
    sound.set_reduced(true)
    sound.set_captions(true)
    await create_timer(.3).timeout
    sound.load_settings()
    assert(sound.levels.Music == .3 and sound.levels.Master == .8 and sound.reduced and sound.captions)
    fixture.load(sound.settings_path)
    assert(fixture.get_value("graphics","fps") == 60 and fixture.get_value("network","server") == "https://example.invalid/api/v1")
    var descriptions: Array[String] = []
    sound.caption_requested.connect(func(words): descriptions.append(words))
    assert(sound.cue("footstep"))
    assert(not sound.cue("footstep"),"Same-frame footstep duplicates must be suppressed")
    assert(descriptions == ["Footsteps"])
    for key in sound.CUES:
        sound.cue(key)
    assert(sound.voices.filter(func(voice): return voice.playing).size() <= sound.VOICE_LIMIT)
    sound.set_backgrounded(true)
    assert(sound.loops.all(func(stream): return stream.stream_paused))
    assert(sound.voices.all(func(voice): return not voice.playing) and not sound.cue("ui"))
    sound.set_backgrounded(false)
    assert(sound.loops.all(func(stream): return not stream.stream_paused))
    assert(sound.voices.all(func(voice): return not voice.playing),"Resume must not replay interrupted cues")
    # Capture the actual mixer output, including bus mute, not just player flags.
    sound.set_volume("Music",0)
    sound.set_volume("Ambience",0)
    sound.set_volume("Spells",1)
    sound.set_reduced(false)
    var capture = AudioEffectCapture.new()
    capture.buffer_length = .5
    var capture_index = AudioServer.get_bus_effect_count(0)
    AudioServer.add_bus_effect(0,capture)
    await create_timer(.1).timeout
    capture.clear_buffer()
    sound.cooldowns.clear()
    assert(sound.cue("cast"))
    await create_timer(.2).timeout
    var audible = capture.get_buffer(capture.get_frames_available())
    var peak := 0.0
    for sample in audible:
        peak = maxf(peak,maxf(absf(sample.x),absf(sample.y)))
    print("AUDIO_MIX_PEAK=",peak," FRAMES=",audible.size())
    assert(peak > .005 and peak < .9,"The actual cue mix must be audible with headroom")
    sound.set_volume("Master",0)
    await create_timer(.1).timeout
    capture.clear_buffer()
    await create_timer(.1).timeout
    var muted = capture.get_buffer(capture.get_frames_available())
    # Capture is pre-fader; test mute on a child bus so Master capture sees silence.
    sound.set_volume("Master",.8)
    sound.set_volume("Spells",0)
    await create_timer(.1).timeout
    capture.clear_buffer()
    await create_timer(.1).timeout
    muted = capture.get_buffer(capture.get_frames_available())
    var muted_peak := 0.0
    for sample in muted:
        muted_peak = maxf(muted_peak,maxf(absf(sample.x),absf(sample.y)))
    assert(not muted.is_empty() and muted_peak < .0001,"Muted spell bus must produce silence")
    # Exercise the full pool with every cue. The master limiter keeps overlap bounded.
    sound.set_volume("Spells",1)
    for voice in sound.voices:
        voice.stop()
    sound.cooldowns.clear()
    for key in sound.CUES:
        sound.cue(key)
    capture.clear_buffer()
    await create_timer(.25).timeout
    var overlap = capture.get_buffer(capture.get_frames_available())
    var overlap_peak := 0.0
    for sample in overlap:
        overlap_peak = maxf(overlap_peak,maxf(absf(sample.x),absf(sample.y)))
    assert(overlap_peak > .01 and overlap_peak <= .892,"Overlapping cues must retain master headroom")
    print("AUDIO_OVERLAP_PEAK=",overlap_peak)
    AudioServer.remove_bus_effect(0,capture_index)
    sound.set_world(false)
    for frame in 90:
        sound._process(1.0/30)
    assert(sound.loops.all(func(stream): return not stream.playing))
    # Real UI dispatch: keyboard changes on a focused slider reach the live bus.
    var app = load("res://scenes/app/bootstrap.tscn").instantiate()
    root.add_child(app)
    app.start_preview()
    app.session.show_audio_settings()
    await process_frame
    var panel = app.session.hud.panel_content.get_child(0)
    assert(panel.sliders.size() == 7 and panel.sliders.Master.size.y >= 56)
    panel.sliders.Master.grab_focus()
    for pressed in [true,false]:
        var key = InputEventKey.new()
        key.keycode = KEY_HOME
        key.pressed = pressed
        root.push_input(key,true)
    await process_frame
    assert(AudioServer.is_bus_mute(0) and panel.sliders.Master.value == 0)
    sound.captions = true
    sound.caption_requested.emit("A warm seam closes")
    assert(app.session.hud.sound_caption.visible and app.session.hud.sound_caption.text == "A warm seam closes")
    app.queue_free()
    await process_frame
    sound.set_world(false)
    for frame in 90:
        sound._process(1.0/30)
    sound.save_timer.stop()
    DirAccess.remove_absolute(sound.settings_path)
    sound.settings_path = config_path
    sound.load_settings()
    sound.set_process(true)
    print("AUDIO_FRAMEWORK_PASS: actual mix/mute, bounded voices, loops/transitions, captions, persistence, background/resume")
    await create_timer(.15).timeout
    quit.call_deferred()
