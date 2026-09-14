class_name AudioPanel
extends VBoxContainer
var sliders: Dictionary = {}
var sound
var reduced_button: CheckButton
var caption_button: CheckButton

func build() -> void:
    sound = get_node("/root/Soundscape")
    for bus in sound.DEFAULTS:
        var row = HBoxContainer.new()
        add_child(row)
        var label = TideUI.label("%s · %s%%" % [bus,roundi(sound.levels[bus]*100)],19)
        label.custom_minimum_size.x = 180
        label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
        row.add_child(label)
        var slider = HSlider.new()
        slider.min_value = 0
        slider.max_value = 100
        slider.step = 1
        slider.value = sound.levels[bus]*100
        slider.custom_minimum_size = Vector2(250,56)
        slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        slider.tooltip_text = bus+" volume"
        slider.value_changed.connect(func(value):
            label.text = "%s · %s%%" % [bus,roundi(value)]
            sound.set_volume(bus,value/100.0))
        row.add_child(slider)
        sliders[bus] = slider
    reduced_button = CheckButton.new()
    reduced_button.mouse_filter = Control.MOUSE_FILTER_PASS
    reduced_button.text = "Softer spell and creature sounds"
    reduced_button.custom_minimum_size.y = 56
    reduced_button.button_pressed = sound.reduced
    reduced_button.toggled.connect(sound.set_reduced)
    add_child(reduced_button)
    caption_button = CheckButton.new()
    caption_button.mouse_filter = Control.MOUSE_FILTER_PASS
    caption_button.text = "Sound captions"
    caption_button.custom_minimum_size.y = 56
    caption_button.button_pressed = sound.captions
    caption_button.toggled.connect(sound.set_captions)
    add_child(caption_button)
    add_child(TideUI.paragraph("Volume changes save automatically. All quest and combat information also appears as text.",17))
    if OS.is_debug_build():
        print("VT_AUDIO_SETTINGS_READY")
