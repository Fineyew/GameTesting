class_name CommercePanel
extends VBoxContainer
signal buy_requested(listing_key: String)
signal equip_requested(slot: String, item_key: Variant)
signal vendor_requested
signal bag_requested
var buy_buttons: Dictionary = {}
var equip_buttons: Dictionary = {}
var unequip_button: Button
var browse_button: Button
var search: LineEdit

func build(view: Dictionary, offline: bool, feedback := "") -> void:
    var character = view.character
    var shop = view.get("shop",{})
    add_child(TideUI.label("Shell chits · %s" % int(character.get("wallet",{}).get("shell_chits",0)),22,TideUI.GOLD))
    if shop.is_empty():
        browse_button = TideUI.button("Browse Mara's supply cart",vendor_requested.emit,true)
        add_child(browse_button)
    if not feedback.is_empty():
        add_child(TideUI.paragraph(feedback,20))
    if offline:
        add_child(TideUI.paragraph("Preview · Sign in to buy supplies and save equipment.",17))
    add_child(TideUI.paragraph("Equipment Guard · %s\nReduces each incoming hit; adds to Brace and spell protection. Your robe appearance stays yours." % int(view.stats.guard),17))
    if shop.is_empty():
        var equipped = character.get("equipment",{}).get("chest","")
        add_child(TideUI.paragraph("CHEST · " + (GameData.display_name("equipment",equipped) if not equipped.is_empty() else "No equipment"),20))
        if not equipped.is_empty():
            unequip_button = TideUI.button("Unequip · Guard −%s" % int(view.stats.guard),func(): equip_requested.emit("chest",null))
            unequip_button.disabled = offline
            add_child(unequip_button)
        search = TideUI.edit("Search your items")
        add_child(search)
    else:
        add_child(TideUI.button("Open bag & equipment",bag_requested.emit))
    var rows = VBoxContainer.new()
    add_child(rows)
    for item in shop.get("listings",view.items):
        var card = PanelContainer.new()
        card.set_meta("search_name",item.name.to_lower())
        rows.add_child(card)
        var column = VBoxContainer.new()
        card.add_child(column)
        column.add_child(TideUI.paragraph(item.name,23))
        if item.type != "equipment":
            column.add_child(TideUI.paragraph(item.summary,17))
        column.add_child(TideUI.label("%s · Owned ×%s" % ["EQUIPPED" if item.get("equipped",false) else "IN BAG" if item.owned > 0 else "NOT OWNED",int(item.owned)],17,TideUI.GOLD))
        if item.type == "equipment":
            column.add_child(TideUI.paragraph("Chest · Level %s · Guard +%s\nCompared with %s: %s → %s (%+d)" % [int(item.required_level),int(item.guard),item.equipped_name,int(item.current_guard),int(item.guard),int(item.guard_delta)],18))
            if item.owned > 0 and not item.equipped:
                var equip = TideUI.button("Equip · Guard %+d" % int(item.guard_delta),func(): equip_requested.emit(item.slot,item.item_key),true)
                equip.disabled = offline or character.get("level",1) < item.required_level
                column.add_child(equip)
                equip_buttons[item.item_key] = equip
        elif item.item_key == "sunthread_bandage":
            column.add_child(TideUI.paragraph("Item use is not available yet.",17))
        if not shop.is_empty():
            var buy = TideUI.button("Buy ×%s · %s shell chits" % [int(item.quantity),int(item.price)],func(): buy_requested.emit(item.listing_key),true)
            buy.disabled = offline or not item.can_buy
            column.add_child(buy)
            buy_buttons[item.listing_key] = buy
            if not item.reason.is_empty():
                column.add_child(TideUI.paragraph(item.reason,17))
    if rows.get_child_count() == 0:
        rows.add_child(TideUI.paragraph("Your bag is empty. Earn shell chits by helping Mara."))
    if search:
        search.text_changed.connect(func(value):
            for row in rows.get_children():
                row.visible = value.to_lower() in row.get_meta("search_name",""))

static func preview_view(character: Dictionary, shop_key: String) -> Dictionary:
    # Catalog presentation only. Preview never creates inventory or sends commands.
    var result = {"character":character,"stats":{"guard":0},"items":[]}
    if shop_key.is_empty():
        return result
    var shop = GameData.definition("shops",shop_key)
    var listings: Array = []
    for row in shop.rules.listings:
        var definition = GameData.definition("equipment",row.item_key)
        if definition.is_empty():
            definition = GameData.definition("items",row.item_key)
        var item = {"item_key":row.item_key,"name":definition.display.name,"summary":definition.display.summary,"type":definition.type,"owned":0,"listing_key":row.key,"quantity":row.quantity,"price":row.price[0].amount,"can_buy":false,"reason":row.get("unavailable_reason","")}
        if definition.type == "equipment":
            item.merge({"slot":definition.rules.slot,"required_level":definition.rules.required_level,"guard":definition.rules.modifiers[0].value,"current_guard":0,"guard_delta":definition.rules.modifiers[0].value,"equipped":false,"equipped_name":"No chest equipment"})
        listings.append(item)
    result.shop = {"key":shop.key,"name":shop.display.name,"version":shop.version,"listings":listings}
    return result
