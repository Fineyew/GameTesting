extends SceneTree
## Record actual Godot bus output for review. Not a phone/headphone acceptance test.
func _init() -> void:
    call_deferred("run")

func run() -> void:
    var sound = root.get_node("Soundscape")
    sound.settings_path = "user://audio-recording-fixture.cfg"
    sound.load_settings()
    var recorder = AudioEffectRecord.new()
    recorder.format = AudioStreamWAV.FORMAT_16_BITS
    var index = AudioServer.get_bus_effect_count(0)
    AudioServer.add_bus_effect(0,recorder)
    recorder.set_recording_active(true)
    sound.set_world(true)
    await create_timer(6).timeout
    sound.cue("discovery")
    sound.ducked = true
    await create_timer(2).timeout
    sound.ducked = false
    sound.set_combat(true)
    sound.cue("creature")
    await create_timer(2).timeout
    sound.cue("cast")
    await create_timer(.75).timeout
    sound.cue("impact")
    await create_timer(1.25).timeout
    sound.cue("guard")
    await create_timer(1.5).timeout
    sound.cue("mend")
    await create_timer(1.5).timeout
    sound.set_combat(false)
    await create_timer(2).timeout
    sound.set_backgrounded(true)
    await create_timer(1).timeout
    sound.set_backgrounded(false)
    await create_timer(2).timeout
    sound.set_world(false)
    await create_timer(2).timeout
    recorder.set_recording_active(false)
    var wave = recorder.get_recording()
    assert(wave != null and wave.get_length() > 20)
    assert(wave.save_to_wav("user://dawnreef-audio-engine.wav") == OK)
    AudioServer.remove_bus_effect(0,index)
    await sound.shutdown()
    print("AUDIO_ROUTE_PASS: actual music, duck, combat, cues, background/resume and exit mix")
    quit.call_deferred()
