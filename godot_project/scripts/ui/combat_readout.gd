class_name CombatReadout
extends RefCounted

static func describe(action: String, spells: Dictionary) -> Dictionary:
    if action == "brace":
        return {"name":"Brace","cost":0,"target":"You","effect":"Block 6 damage this beat","family":"Wayfarer"}
    if action == "gather":
        return {"name":"Gather","cost":0,"target":"You","effect":"Gain up to 2 Focus","family":"Wayfarer"}
    var spell = spells.get(action,{})
    var cost := 0
    var effects: Array[String] = []
    var self_target := false
    for value in spell.get("costs",[]):
        cost += int(value.amount)
    for value in spell.get("effects",[]):
        var amount = int(value.get("amount",value.get("power",0)))
        match value.type:
            "deal_damage": effects.append("%s damage%s" % [amount," · pierces armor" if value.get("piercing",false) else ""])
            "restore_vigor":
                effects.append("Restore up to %s Vigor" % amount)
                self_target = true
            "guard":
                effects.append("Block %s this beat" % amount)
                self_target = true
            "bind": effects.append("Weaken this hit by %s" % amount)
            "ward_focus": effects.append("Protect %s Focus this beat" % amount)
            "mark": effects.append("Next strike +%s damage" % amount)
    return {"name":spell.get("name",action.capitalize()),"cost":cost,"target":"You" if self_target else "Foe",
        "effect":" · ".join(effects),"family":TidebeatEffect.PROFILES.get(action,["Wayfarer"])[0]}

static func intent(combat: Dictionary) -> String:
    var next = combat.get("intent",{})
    var power = int(next.get("power",0))
    var words = "%s · %s damage before protection" % [next.get("name","Waiting"),power]
    if int(next.get("guard",0)) > 0:
        words += " · Armor %s" % int(next.guard)
    if int(next.get("focus_drain",0)) > 0:
        words += " · Draws %s Focus" % int(next.focus_drain)
    return words
