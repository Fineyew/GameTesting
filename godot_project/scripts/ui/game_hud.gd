class_name GameHUD
extends Control
signal interact_requested
signal journal_requested
signal inventory_requested
signal folio_requested
signal settings_requested
signal chat_requested
signal recenter_requested
signal panel_closed
var stick: TouchStick
var profile: Label
var progression_label: Label
var connection_label: Label
var quest_label: Label
var interaction: Button
var popup: PanelContainer
var panel_title: Label
var panel_content: VBoxContainer
var modal := false
var sound_caption: Label
var caption_remaining := 0.0

func _ready() -> void:
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    mouse_filter = Control.MOUSE_FILTER_IGNORE
    theme = TideUI.theme()
    var margin = MarginContainer.new()
    margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    for side in ["left","right","top","bottom"]:
        margin.add_theme_constant_override("margin_"+side,24)
    margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
    add_child(margin)
    var column = VBoxContainer.new()
    column.mouse_filter = Control.MOUSE_FILTER_IGNORE
    margin.add_child(column)
    var top = HBoxContainer.new()
    top.mouse_filter = Control.MOUSE_FILTER_IGNORE
    column.add_child(top)
    var plaque = PanelContainer.new()
    top.add_child(plaque)
    var labels = VBoxContainer.new()
    plaque.add_child(labels)
    labels.add_child(TideUI.label("DAWNREEF ATOLL",16,TideUI.GOLD))
    profile = TideUI.label("Wayfarer",24)
    labels.add_child(profile)
    progression_label = TideUI.label("",15,TideUI.MUTED)
    labels.add_child(progression_label)
    connection_label = TideUI.label("Connecting…",16,TideUI.MUTED)
    labels.add_child(connection_label)
    var spacer = Control.new()
    spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
    top.add_child(spacer)
    for spec in [["Folio",folio_requested],["Journal",journal_requested],["Settings",settings_requested]]:
        var action = TideUI.button(spec[0],spec[1].emit)
        action.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
        top.add_child(action)
    var air = Control.new()
    air.size_flags_vertical = Control.SIZE_EXPAND_FILL
    air.mouse_filter = Control.MOUSE_FILTER_IGNORE
    column.add_child(air)
    var bottom = HBoxContainer.new()
    bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
    column.add_child(bottom)
    stick = TouchStick.new()
    bottom.add_child(stick)
    var middle = VBoxContainer.new()
    middle.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    middle.size_flags_vertical = Control.SIZE_SHRINK_END
    middle.mouse_filter = Control.MOUSE_FILTER_IGNORE
    bottom.add_child(middle)
    quest_label = TideUI.paragraph("Find Mara beside the Lantern Well.")
    quest_label.add_theme_color_override("font_shadow_color",TideUI.INK)
    quest_label.add_theme_constant_override("shadow_offset_x",2)
    quest_label.add_theme_constant_override("shadow_offset_y",2)
    middle.add_child(quest_label)
    middle.add_child(TideUI.paragraph("Move: left thumb / WASD   •   Look: drag right / right mouse",14))
    var actions = GridContainer.new()
    actions.columns = 2
    actions.size_flags_vertical = Control.SIZE_SHRINK_END
    bottom.add_child(actions)
    interaction = TideUI.button("Explore",interact_requested.emit,true)
    interaction.custom_minimum_size.x = 156
    actions.add_child(interaction)
    actions.add_child(TideUI.button("Bag",inventory_requested.emit))
    actions.add_child(TideUI.button("Recenter",recenter_requested.emit))
    actions.add_child(TideUI.button("Say hello",chat_requested.emit))
    sound_caption = TideUI.label("",19,TideUI.PAPER)
    sound_caption.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
    sound_caption.offset_left = -260
    sound_caption.offset_right = 260
    sound_caption.offset_top = 124
    sound_caption.offset_bottom = 152
    sound_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
    sound_caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
    sound_caption.add_theme_color_override("font_shadow_color",TideUI.INK)
    sound_caption.add_theme_constant_override("shadow_offset_x",2)
    sound_caption.add_theme_constant_override("shadow_offset_y",2)
    add_child(sound_caption)
    sound_caption.hide()
    Soundscape.caption_requested.connect(show_sound_caption)
    popup = PanelContainer.new()
    popup.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
    popup.offset_left = -330
    popup.offset_right = 330
    popup.offset_top = -285
    popup.offset_bottom = 285
    add_child(popup)
    var panel_column = VBoxContainer.new()
    popup.add_child(panel_column)
    var header = HBoxContainer.new()
    panel_column.add_child(header)
    panel_title = TideUI.label("Journal",27)
    panel_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    header.add_child(panel_title)
    header.add_child(TideUI.button("Close",close_panel))
    var scroll = ScrollContainer.new()
    scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
    scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
    panel_column.add_child(scroll)
    panel_content = VBoxContainer.new()
    panel_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    scroll.add_child(panel_content)
    popup.hide()

func open_panel(title: String) -> VBoxContainer:
    panel_title.text = title
    for child in panel_content.get_children():
        # Touch dispatch can still hold the emitting control after its callback.
        # Hide it now; queue_free keeps it in the tree until dispatch has finished.
        child.hide()
        child.queue_free()
    panel_content.get_parent().set_deferred("scroll_vertical",0)
    modal = true
    stick.release()
    popup.show()
    return panel_content

func close_panel() -> void:
    modal = false
    popup.hide()
    panel_closed.emit()

func set_character(character: Dictionary, preview: bool) -> void:
    profile.text = "%s · Level %s" % [character.get("name","Wayfarer"),int(character.get("level",1))]
    var level = int(character.get("level",1))
    var progression = GameData.definition("progression","wayfarer").get("rules",{})
    var thresholds = progression.get("level_thresholds",[0,100])
    var next_xp = int(thresholds[level]) if level < thresholds.size() else int(thresholds[-1])+(level-thresholds.size()+1)*int(progression.get("continued_level_step",100))
    progression_label.text = "XP %s / %s · %s affinity" % [int(character.get("experience",0)),next_xp,character.get("affinity","lanterncraft").capitalize()]
    if preview:
        connection_label.text = "OFFLINE PREVIEW · progress is not saved"
        quest_label.text = "Explore Dawnreef. Sign in for quests and combat."
    else:
        quest_label.text = "Speak with Mara beside the Lantern Well."
        for key in character.get("quest_state",{}):
            var progress = character.quest_state[key]
            if progress.get("completed",false):
                continue
            for objective in GameData.definition("quests",key).get("rules",{}).get("objectives",[]):
                if progress.get("objectives",{}).get(objective.key,0) < objective.quantity:
                    quest_label.text = objective.get("label",GameData.display_name("quests",key))
                    return

func show_sound_caption(words: String) -> void:
    sound_caption.text = words
    sound_caption.visible = not words.is_empty()
    caption_remaining = 2.0

func _process(delta: float) -> void:
    if caption_remaining > 0:
        caption_remaining -= delta
        if caption_remaining <= 0:
            sound_caption.hide()
