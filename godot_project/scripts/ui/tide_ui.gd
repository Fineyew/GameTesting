class_name TideUI
extends RefCounted
const INK = Color("102c36")
const PAPER = Color("f3ead5")
const MUTED = Color("b5c6bf")
const GOLD = Color("d6b875")

static func style(color: Color, radius := 14, border := Color.TRANSPARENT) -> StyleBoxFlat:
    var box = StyleBoxFlat.new()
    box.bg_color = color
    box.set_corner_radius_all(radius)
    box.set_content_margin_all(16)
    box.border_color = border
    box.set_border_width_all(1 if border.a > 0 else 0)
    return box

static func theme() -> Theme:
    var result = Theme.new()
    result.default_font_size = 20
    result.set_color("font_color","Label",PAPER)
    result.set_color("font_color","Button",PAPER)
    result.set_color("font_color","LineEdit",PAPER)
    result.set_color("font_placeholder_color","LineEdit",MUTED)
    result.set_stylebox("normal","Button",style(Color("234951"),14,Color("42696a")))
    result.set_stylebox("hover","Button",style(Color("315e61")))
    result.set_stylebox("pressed","Button",style(Color("507b73")))
    result.set_stylebox("disabled","Button",style(Color("203b43")))
    result.set_stylebox("focus","Button",style(Color.TRANSPARENT,14,GOLD))
    result.set_stylebox("normal","LineEdit",style(Color("14313c"),12,Color("52716f")))
    result.set_stylebox("focus","LineEdit",style(Color("14313c"),12,GOLD))
    var panel = style(Color(.055,.14,.18,.96),18,Color("657666"))
    panel.shadow_color = Color(0.015,.03,.04,.28)
    panel.shadow_size = 8
    panel.shadow_offset = Vector2(0,4)
    result.set_stylebox("panel","PanelContainer",panel)
    result.set_constant("separation","VBoxContainer",12)
    result.set_constant("separation","HBoxContainer",12)
    return result

static func label(words: String, font_size := 20, color := PAPER) -> Label:
    var node = Label.new()
    node.text = words
    node.add_theme_font_size_override("font_size",font_size)
    node.add_theme_color_override("font_color",color)
    return node

static func paragraph(words: String, font_size := 20) -> Label:
    var node = label(words,font_size)
    node.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return node

static func button(words: String, callback: Callable, primary := false) -> Button:
    var node = Button.new()
    node.text = words
    node.custom_minimum_size.y = 56
    node.pressed.connect(callback)
    if primary:
        node.add_theme_stylebox_override("normal",style(GOLD))
        node.add_theme_color_override("font_color",INK)
    return node

static func edit(placeholder: String, secret := false) -> LineEdit:
    var node = LineEdit.new()
    node.placeholder_text = placeholder
    node.secret = secret
    node.max_length = 128 if secret else 254
    node.custom_minimum_size.y = 54
    return node

static func option(items: Array) -> OptionButton:
    var node = OptionButton.new()
    node.custom_minimum_size.y = 54
    for item in items:
        node.add_item(item)
    return node
