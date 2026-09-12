class_name FolioPanel
extends VBoxContainer
signal prepare_requested(spells: Array)
var selected: Array = []
var saved: Array = []
var capacity := 6
var choices: Dictionary = {}
var status: Label
var save_button: Button

func build(character: Dictionary, offline: bool) -> void:
    capacity = int(character.get("folio_capacity",6))
    saved = character.get("folio",[]).duplicate()
    selected = saved.duplicate()
    status = TideUI.paragraph("")
    add_child(status)
    add_child(TideUI.paragraph("Prepare up to %s spells before an encounter. Brace and Gather are always available and use no slots." % capacity,17))
    if offline:
        add_child(TideUI.paragraph("Sign in to learn spells with Mara and save your folio."))
    else:
        save_button = TideUI.button("Save prepared spells",func(): prepare_requested.emit(selected.duplicate()),true)
        add_child(save_button)
    for spell in GameData.definitions.values():
        if spell.type != "spells":
            continue
        var key = spell.key
        var learned = key in character.get("known_spells",[]) and not offline
        var card = PanelContainer.new()
        add_child(card)
        var column = VBoxContainer.new()
        card.add_child(column)
        column.add_child(TideUI.paragraph("%s · %s Focus" % [spell.display.name,focus_cost(spell.rules)],22))
        column.add_child(TideUI.paragraph(effect_text(spell.rules),18))
        if learned:
            var action = TideUI.button("",toggle_spell.bind(key))
            column.add_child(action)
            choices[key] = action
        else:
            column.add_child(TideUI.paragraph("NOT LEARNED · " + source_text(key),17))
    refresh()
    if offline:
        status.text = "Spell collection preview"

func toggle_spell(key: String) -> void:
    if key not in choices:
        return
    if key in selected:
        selected.erase(key)
    elif selected.size() < capacity:
        selected.append(key)
    refresh()

func refresh() -> void:
    status.text = "Prepared · %s / %s%s" % [selected.size(),capacity," · Unsaved changes" if selected != saved else " · Saved"]
    if save_button:
        save_button.disabled = selected.is_empty() or selected == saved
    for key in choices:
        var prepared = key in selected
        choices[key].text = "Prepared %s · Remove" % (selected.find(key)+1) if prepared else "Learned · Prepare"
        choices[key].disabled = not prepared and selected.size() >= capacity
        choices[key].add_theme_color_override("font_color",TideUI.GOLD if prepared else TideUI.PAPER)

static func focus_cost(rules: Dictionary) -> int:
    var total := 0
    for cost in rules.get("costs",[]):
        total += int(cost.amount)
    return total

static func effect_text(rules: Dictionary) -> String:
    var words: Array[String] = []
    for effect in rules.get("effects",[]):
        var amount = effect.get("amount",effect.get("power",0))
        match effect.type:
            "deal_damage": words.append("Deal %s damage" % amount)
            "restore_vigor": words.append("Restore %s Vigor" % amount)
            "bind": words.append("Reduce this intent by %s" % amount)
            "guard": words.append("Absorb %s damage this beat" % amount)
            "mark": words.append("Next damaging spell gains %s damage; marks stack to 12" % amount)
    return ". ".join(words) + "."

static func source_text(spell_key: String) -> String:
    for quest in GameData.definitions.values():
        if quest.type != "quests":
            continue
        for reward in quest.rules.get("rewards",[]):
            if reward.type == "learn_spell" and reward.spell_key == spell_key:
                return "Mara's lesson: " + quest.display.name
    return "Learned when your journey begins."
