class_name PlaySession
extends Node
signal return_requested
var world: DawnreefWorld
var character: Dictionary
var preview := false
var player: WayfarerController
var camera: OrbitRig
var hud: GameHUD
var connection: WorldConnection
var remotes: Dictionary = {}
var nearest := ""
var pending_action: Dictionary = {}
var busy := false
var refresh_elapsed := 0.0
var dialogue: Dictionary = {}
var pending_folio: Dictionary = {}
var folio_panel: FolioPanel
var commerce_panel: CommercePanel
var commerce_view: Dictionary = {}
var pending_commerce: Dictionary = {}
var commerce_shop := ""
var commerce_error := ""
var short_spell_effects := false
var application_active := true

func _notification(what: int) -> void:
    if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_APPLICATION_FOCUS_OUT:
        application_active = false
        if is_instance_valid(player):
            hud.stick.release()
            player.input_axis = Vector2.ZERO
            player.velocity.x = 0
            player.velocity.z = 0
            camera.finger = -1
        if is_instance_valid(connection):
            connection.axis = Vector2.ZERO
    elif what == NOTIFICATION_APPLICATION_RESUMED or what == NOTIFICATION_APPLICATION_FOCUS_IN:
        application_active = true

func begin(zone: DawnreefWorld, profile: Dictionary, offline: bool) -> void:
    world = zone
    character = profile
    preview = offline
    var settings = ConfigFile.new()
    settings.load("user://settings.cfg")
    short_spell_effects = settings.get_value("accessibility","short_spell_effects",false)
    player = preload("res://scenes/player/wayfarer.tscn").instantiate()
    world.add_child(player)
    player.setup(character.get("appearance",{}),world.geometry)
    var at = character.get("position",{"x":0,"z":4})
    player.position = Vector3(at.x,.1,at.z)
    player.networked = not preview
    camera = OrbitRig.new()
    world.add_child(camera)
    camera.target = player
    camera.arm.add_excluded_object(player.get_rid())
    hud = GameHUD.new()
    add_child(hud)
    hud.set_character(character,preview)
    hud.interact_requested.connect(interact)
    hud.journal_requested.connect(show_journal)
    hud.inventory_requested.connect(show_inventory)
    hud.folio_requested.connect(show_folio)
    hud.settings_requested.connect(show_settings)
    hud.chat_requested.connect(show_chat)
    hud.recenter_requested.connect(camera.recenter)
    ApiClient.request_failed.connect(_commerce_failed)
    if not preview:
        connection = WorldConnection.new()
        add_child(connection)
        connection.snapshot_received.connect(_snapshot)
        connection.state_changed.connect(func(message): hud.connection_label.text = message)
        connection.start(character.id)
        if character.get("encounter",{}).get("state") == "active":
            show_combat()

func _process(delta: float) -> void:
    if not is_instance_valid(player):
        return
    var axis = hud.stick.axis
    axis += Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT))-float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN))-float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
    if not Input.get_connected_joypads().is_empty():
        var pad = Input.get_connected_joypads()[0]
        var joy = Vector2(Input.get_joy_axis(pad,JOY_AXIS_LEFT_X),Input.get_joy_axis(pad,JOY_AXIS_LEFT_Y))
        if joy.length() > .2:
            axis += joy
    axis = axis.limit_length().rotated(-camera.yaw)
    var fighting = character.get("encounter",{}).get("state") == "active"
    player.enabled = application_active and not busy and not hud.modal and not fighting and (preview or connection.connected)
    player.input_axis = axis
    camera.enabled = application_active and not busy and not hud.modal
    if connection:
        connection.axis = axis if player.enabled else Vector2.ZERO
    nearest = ""
    var distance = 3.2
    for key in world.geometry.interactions:
        var at = world.geometry.interactions[key]
        var candidate = Vector2(player.position.x-at[0],player.position.z-at[1]).length()
        if candidate < distance:
            nearest = key
            distance = candidate
    hud.interaction.text = {"mara_lanternwright":"Talk to Mara","fog_thorn_lurker":"Encounter","sunthread_reeds":"Inspect reeds","saltglass_cistern":"Inspect gate"}.get(nearest,"Explore")
    for remote in remotes.values():
        var before = remote.avatar.position
        remote.avatar.position = before.lerp(remote.target,minf(1,delta*10))
        var motion = remote.avatar.position-before
        remote.avatar.travel_speed = motion.length()/maxf(delta,.001)
        remote.avatar.walking = motion.length() > .003
        if remote.avatar.walking:
            remote.avatar.rotation.y = lerp_angle(remote.avatar.rotation.y,atan2(-motion.x,-motion.z),delta*10)
    if not preview:
        refresh_elapsed += delta
        if refresh_elapsed > 600:
            refresh_elapsed = 0
            _refresh_auth()

func _snapshot(frame: Dictionary) -> void:
    var present: Array = []
    for remote in frame.get("players",[]):
        if remote.id == character.id:
            player.reconcile(Vector3(remote.x,0,remote.z))
            continue
        present.append(remote.id)
        if not remotes.has(remote.id):
            var avatar = WayfarerAvatar.new()
            world.add_child(avatar)
            avatar.build(remote.appearance)
            avatar.position = Vector3(remote.x,0,remote.z)
            var name_label = ReefKit.label(avatar,remote.name,Vector3(0,2.3,0))
            remotes[remote.id] = {"avatar":avatar,"label":name_label,"target":avatar.position}
        remotes[remote.id].target = Vector3(remote.x,0,remote.z)
        remotes[remote.id].label.text = remote.name + ("\n" + remote.bubble if not remote.bubble.is_empty() else "")
    for identity in remotes.keys():
        if not identity in present:
            remotes[identity].avatar.queue_free()
            remotes.erase(identity)
    hud.connection_label.text = "Connected · %s Wayfarer%s nearby" % [frame.players.size(),"s" if frame.players.size()!=1 else ""]

func interact() -> void:
    if busy:
        return
    match nearest:
        "mara_lanternwright":
            if preview:
                var panel = hud.open_panel("Mara Lanternwright")
                panel.add_child(TideUI.paragraph("The well keeps Dawnreef steady above the Glimmerdeep. Tonight its light is answering something beneath the reef."))
                panel.add_child(TideUI.paragraph("Sign in to help Mara and save your journey."))
                panel.add_child(TideUI.button("Browse supplies",show_vendor))
            else:
                open_dialogue()
        "fog_thorn_lurker":
            if preview:
                hud.open_panel("A creature in the mist").add_child(TideUI.paragraph("Combat and rewards require an online character. Return to sign in when your server is available."))
            else:
                start_encounter()
        "sunthread_reeds", "saltglass_cistern":
            if preview:
                var discovery = GameData.definition("zones","dawnreef_atoll").rules.discoveries[nearest]
                hud.open_panel(discovery.title).add_child(TideUI.paragraph(discovery.text))
            else:
                inspect_landmark(nearest)
        _:
            hud.quest_label.text = "Move close to Mara, the lurker, the reeds, or the cistern gate."

func open_dialogue(npc_key := "mara_lanternwright") -> void:
    if busy:
        return
    busy = true
    hud.open_panel("Speaking with Mara…").add_child(TideUI.paragraph("Listening…"))
    var result = await ApiClient.post_json("/world/characters/%s/npcs/%s/dialogue" % [character.id,npc_key],{})
    busy = false
    apply_dialogue_result(result)

func choose_dialogue(option_key: String) -> void:
    if busy or dialogue.is_empty():
        return
    busy = true
    var result = await ApiClient.post_json("/world/characters/%s/npcs/%s/dialogue/choose" % [character.id,dialogue.npc_key],{"conversation_id":dialogue.id,"option_key":option_key})
    busy = false
    apply_dialogue_result(result)

func apply_dialogue_result(result: Dictionary) -> void:
    if result.is_empty():
        dialogue = {}
        var unavailable = hud.open_panel("Conversation paused")
        unavailable.add_child(TideUI.paragraph("Check your connection and stay near Mara, then speak again. Your saved quest progress is safe."))
        unavailable.add_child(TideUI.button("Speak again",open_dialogue))
        return
    var newly_learned: Array = []
    for key in result.character.get("known_spells",[]):
        if key not in character.get("known_spells",[]):
            newly_learned.append(GameData.display_name("spells",key))
    character = result.character
    hud.set_character(character,preview)
    dialogue = result.dialogue if result.get("dialogue") is Dictionary else {}
    if dialogue.is_empty():
        hud.close_panel()
        return
    var panel = hud.open_panel(dialogue.speaker)
    if not newly_learned.is_empty():
        panel.add_child(TideUI.paragraph("SPELL LEARNED · " + ", ".join(newly_learned),24))
        panel.add_child(TideUI.button("Open Folio to prepare",show_folio,true))
    panel.add_child(TideUI.paragraph(dialogue.text))
    for option in dialogue.options:
        panel.add_child(TideUI.button(option.text,choose_dialogue.bind(option.key),true))
    if dialogue.options.is_empty():
        panel.add_child(TideUI.button("Until next time",hud.close_panel,true))
    panel.add_child(TideUI.button("Browse Mara's supply cart",show_vendor))

func inspect_landmark(key: String) -> void:
    if busy:
        return
    busy = true
    hud.open_panel("Listening…").add_child(TideUI.paragraph("Let the reef settle."))
    var result = await ApiClient.post_json("/world/characters/%s/interactions/%s/inspect" % [character.id,key],{})
    busy = false
    if result.is_empty():
        hud.open_panel("Could not listen").add_child(TideUI.paragraph("Move closer while connected, then try again."))
        return
    character = result.character
    hud.set_character(character,preview)
    hud.open_panel(result.discovery.title).add_child(TideUI.paragraph(result.discovery.text))

func accept_quest() -> void:
    busy = true
    var result = await ApiClient.post_json("/world/characters/%s/quests/lantern_well_first_light/accept" % character.id,{})
    busy = false
    if not result.is_empty():
        character = result
        hud.set_character(character,preview)
        hud.close_panel()

func command_id() -> String:
    return Crypto.new().generate_random_bytes(16).hex_encode()

func start_encounter() -> void:
    busy = true
    hud.open_panel("Entering encounter…").add_child(TideUI.paragraph("Listening for the creature's first intent."))
    var result = await ApiClient.post_json("/world/characters/%s/encounters" % character.id,{"enemy_key":"fog_thorn_lurker"},command_id())
    busy = false
    if not result.is_empty():
        character = result.character
        show_combat()
    else:
        hud.open_panel("Encounter unavailable").add_child(TideUI.paragraph("Check the connection, move close to the lurker, then try again."))

func show_combat() -> void:
    var combat = character.get("encounter",{})
    if combat.is_empty():
        return
    var panel = hud.open_panel("Tidebeat · " + combat.enemy_name)
    panel.add_child(TideUI.paragraph("Your Vigor %s / 30     Focus %s / 6\nLurker Vigor %s / %s     Beat %s" % [combat.player_vigor,combat.focus,combat.enemy_vigor,combat.enemy_max_vigor,combat.round],22))
    if combat.state == "active":
        panel.add_child(TideUI.paragraph("NEXT INTENT · %s · %s damage" % [combat.intent.name,combat.intent.power]))
        if combat.get("equipment_guard",0) > 0:
            panel.add_child(TideUI.paragraph("Equipment Guard · %s less damage per hit" % int(combat.equipment_guard),17))
        if not pending_action.is_empty():
            panel.add_child(TideUI.paragraph("The result was not received. Retry the same cast safely."))
            panel.add_child(TideUI.button("Retry cast",retry_action,true))
            panel.add_child(TideUI.button("Reload encounter",reload_character))
        else:
            var grid = GridContainer.new()
            grid.columns = 2
            panel.add_child(grid)
            for key in combat.spells:
                var spell = combat.spells[key]
                var cost = 0
                for entry in spell.get("costs",[]):
                    cost += entry.amount
                var button = TideUI.button("%s · %s Focus" % [spell.name,cost],cast.bind(key))
                button.disabled = cost > combat.focus
                button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
                grid.add_child(button)
            grid.add_child(TideUI.button("Brace · block 6",cast.bind("brace")))
            grid.add_child(TideUI.button("Gather · +2 Focus",cast.bind("gather")))
    else:
        panel.add_child(TideUI.label("Victory · rewards saved" if combat.state=="victory" else "Recovered at the Lantern Well",22,TideUI.GOLD))
        panel.add_child(TideUI.button("Return to Dawnreef",hud.close_panel,true))
    panel.add_child(TideUI.paragraph("\n".join(combat.log.slice(-4)),17))

func cast(action: String) -> void:
    if busy:
        return
    pending_action = {"key":command_id(),"payload":{"encounter_id":character.encounter.id,"action":action,"expected_round":character.encounter.round}}
    retry_action()

func retry_action() -> void:
    if busy or pending_action.is_empty():
        return
    busy = true
    hud.open_panel("Casting…").add_child(TideUI.paragraph("Your action is being resolved."))
    var result = await ApiClient.post_json("/world/characters/%s/encounters/actions" % character.id,pending_action.payload,pending_action.key)
    if not result.is_empty():
        var action: String = pending_action.payload.action
        pending_action.clear()
        character = result.character
        hud.set_character(character,preview)
        if action == "glimmer_spark" and not short_spell_effects:
            await present_glimmer()
        else:
            world.spell_impact(action)
    busy = false
    show_combat()

func present_glimmer() -> void:
    # This is presentation of a confirmed result. Damage/rewards never come from VFX.
    hud.close_panel()
    hud.hide()
    var target = world.enemy.global_position + Vector3.UP
    var origin = player.global_position + Vector3.UP*1.45
    var flat = Vector3(target.x-origin.x,0,target.z-origin.z)
    if flat.length() > .02:
        player.avatar.look_at(Vector3(target.x,player.avatar.global_position.y,target.z))
    player.avatar.play_cast()
    var frame = Camera3D.new()
    world.add_child(frame)
    var middle = origin.lerp(target,.5)
    var framed = OrbitRig.pair_frame(world.get_world_3d(),origin,target,player.get_rid())
    if framed.is_finite():
        frame.position = framed
        frame.look_at(middle)
    else:
        frame.global_transform = camera.camera.global_transform
    frame.fov = 60
    frame.make_current()
    world.glimmer_spark(origin,target)
    await get_tree().create_timer(GlimmerPresentation.DURATION).timeout
    camera.camera.make_current()
    frame.queue_free()
    hud.show()

func reload_character() -> void:
    if busy:
        return
    busy = true
    var result = await ApiClient.get_json("/world/characters/"+character.id)
    busy = false
    if not result.is_empty():
        character = result
        pending_action.clear()
        show_combat()

func show_journal() -> void:
    if character.get("encounter",{}).get("state") == "active":
        show_combat()
        return
    var panel = hud.open_panel("Journal · Dawnreef")
    if character.get("quest_state",{}).is_empty():
        panel.add_child(TideUI.paragraph("Speak with Mara to begin your first journey."))
    for key in character.get("quest_state",{}):
        var progress = character.quest_state[key]
        var definition = GameData.definition("quests",key)
        panel.add_child(TideUI.label(GameData.display_name("quests",key),22,TideUI.GOLD))
        if progress.get("completed",false):
            panel.add_child(TideUI.paragraph("Completed · rewards saved"))
        else:
            for objective in definition.get("rules",{}).get("objectives",[]):
                var done = progress.get("objectives",{}).get(objective.key,0)
                panel.add_child(TideUI.paragraph("%s · %s/%s" % [objective.get("label",objective.key.replace("_"," ")),done,objective.quantity]))
    panel.add_child(TideUI.paragraph("Auralis is a world of floating reefs. The Lantern Wells keep them steady. Your Veilmark can hear what moves beneath them."))

func show_folio() -> void:
    if busy:
        return
    if character.get("encounter",{}).get("state") == "active":
        show_combat()
        return
    if not pending_folio.is_empty():
        folio_recovery()
        return
    if not preview:
        busy = true
        hud.open_panel("Opening Folio…").add_child(TideUI.paragraph("Reading your saved spells."))
        var result = await ApiClient.get_json("/world/characters/"+character.id)
        busy = false
        if result.is_empty():
            hud.open_panel("Folio unavailable").add_child(TideUI.button("Try again",show_folio))
            return
        character = result
        hud.set_character(character,preview)
        if character.get("encounter",{}).get("state") == "active":
            show_combat()
            return
    var panel = hud.open_panel("Wayfarer's Folio")
    folio_panel = FolioPanel.new()
    panel.add_child(folio_panel)
    folio_panel.build(character,preview)
    folio_panel.prepare_requested.connect(prepare_folio)
    if OS.is_debug_build():
        print("VT_FOLIO_READY")

func prepare_folio(spells: Array) -> void:
    if busy or preview or not pending_folio.is_empty():
        return
    pending_folio = {"key":command_id(),"payload":{"spells":spells.duplicate(),"expected_revision":int(character.folio_revision)}}
    await retry_folio()

func retry_folio() -> void:
    if busy or pending_folio.is_empty():
        return
    busy = true
    hud.open_panel("Saving Folio…").add_child(TideUI.paragraph("Preparing your chosen spells."))
    var result = await ApiClient.post_json("/world/characters/%s/folio" % character.id,pending_folio.payload,pending_folio.key)
    busy = false
    if result.is_empty():
        folio_recovery()
        return
    pending_folio.clear()
    # A replayed receipt can predate another session's change. Read current state.
    await show_folio()

func folio_recovery() -> void:
    var panel = hud.open_panel("Folio not confirmed")
    panel.add_child(TideUI.paragraph("The save was not confirmed. Retry the same selection, or reload saved spells if your folio or encounter changed."))
    panel.add_child(TideUI.button("Retry save",retry_folio,true))
    panel.add_child(TideUI.button("Reload saved spells",reload_folio))

func reload_folio() -> void:
    if busy:
        return
    pending_folio.clear()
    await show_folio()

func show_inventory() -> void:
    await show_commerce("")

func show_vendor() -> void:
    await show_commerce(GameData.definition("npcs","mara_lanternwright").rules.shop_key)

func show_commerce(shop_key: String, feedback := "") -> void:
    if busy:
        return
    if character.get("encounter",{}).get("state") == "active":
        show_combat()
        return
    if not pending_commerce.is_empty():
        commerce_recovery()
        return
    commerce_shop = shop_key
    commerce_error = ""
    if preview:
        commerce_view = CommercePanel.preview_view(character,shop_key)
    else:
        busy = true
        hud.open_panel("Checking supplies…").add_child(TideUI.paragraph("Reading your saved bag and current prices."))
        commerce_view = await ApiClient.get_json("/world/characters/%s/%s" % [character.id,"equipment" if shop_key.is_empty() else "shops/"+shop_key])
        busy = false
        if commerce_view.is_empty():
            var failed = hud.open_panel("Supplies unavailable")
            failed.add_child(TideUI.paragraph(commerce_error if not commerce_error.is_empty() else "Check your connection and try again."))
            failed.add_child(TideUI.button("Try again",show_commerce.bind(shop_key,feedback)))
            return
        character = commerce_view.character
        hud.set_character(character,preview)
        if character.get("encounter",{}).get("state") == "active":
            show_combat()
            return
    var panel = hud.open_panel("Bag & equipment" if shop_key.is_empty() else commerce_view.shop.name)
    commerce_panel = CommercePanel.new()
    panel.add_child(commerce_panel)
    commerce_panel.build(commerce_view,preview,feedback)
    commerce_panel.buy_requested.connect(buy_listing)
    commerce_panel.equip_requested.connect(equip_item)
    commerce_panel.vendor_requested.connect(show_vendor)
    commerce_panel.bag_requested.connect(show_inventory)
    if OS.is_debug_build():
        print("VT_BAG_READY" if shop_key.is_empty() else "VT_VENDOR_READY")

func buy_listing(listing_key: String) -> void:
    if busy or preview or not pending_commerce.is_empty():
        return
    pending_commerce = {"key":command_id(),"path":"shops/%s/buy" % commerce_shop,"payload":{"listing_key":listing_key,"quantity":1,"shop_version":int(commerce_view.shop.version),"expected_revision":int(character.commerce_revision)}}
    await retry_commerce()

func equip_item(slot: String, item_key: Variant) -> void:
    if busy or preview or not pending_commerce.is_empty():
        return
    pending_commerce = {"key":command_id(),"path":"equipment","payload":{"slot":slot,"item_key":item_key,"expected_revision":int(character.commerce_revision)}}
    await retry_commerce()

func retry_commerce() -> void:
    if busy or pending_commerce.is_empty():
        return
    busy = true
    commerce_error = ""
    hud.open_panel("Saving supplies…").add_child(TideUI.paragraph("Waiting for confirmation."))
    var result = await ApiClient.post_json("/world/characters/%s/%s" % [character.id,pending_commerce.path],pending_commerce.payload,pending_commerce.key)
    busy = false
    if result.is_empty():
        commerce_recovery()
        return
    var outcome = result.outcome
    var message = "Equipment saved."
    if outcome.has("spent"):
        message = "Purchase saved · %s ×%s · %s shell chits spent." % [GameData.display_name("equipment",outcome.item_key),int(outcome.quantity),int(outcome.spent)]
    pending_commerce.clear()
    # A saved receipt may predate another session's update; always read current state.
    await show_commerce(commerce_shop,message)

func commerce_recovery() -> void:
    var panel = hud.open_panel("Change not confirmed")
    panel.add_child(TideUI.paragraph(commerce_error if not commerce_error.is_empty() else "The result was not received. Retry the same command safely, or reload saved supplies."))
    panel.add_child(TideUI.button("Retry same command",retry_commerce,true))
    panel.add_child(TideUI.button("Reload saved supplies",reload_commerce))

func reload_commerce() -> void:
    if busy:
        return
    pending_commerce.clear()
    await show_commerce(commerce_shop)

func _commerce_failed(endpoint: String, status_code: int, message: String) -> void:
    if "/equipment" not in endpoint and "/shops/" not in endpoint:
        return
    var body = JSON.parse_string(message)
    commerce_error = "Connection interrupted. Retry safely or reload saved supplies."
    if status_code == 401:
        commerce_error = "Your session expired. Return to sign in; saved supplies are safe."
    elif body is Dictionary and body.get("detail") is String:
        commerce_error = body.detail.capitalize()

func show_settings() -> void:
    var panel = hud.open_panel("Settings")
    var frames = TideUI.option(["Battery · 30 FPS","Smooth · 60 FPS"])
    frames.select(1 if Engine.max_fps==60 else 0)
    frames.item_selected.connect(func(index): Engine.max_fps = 60 if index else 30; save_settings())
    panel.add_child(frames)
    var shadow = CheckButton.new()
    shadow.text = "Character and world shadows"
    shadow.custom_minimum_size.y = 56
    shadow.button_pressed = world.sun.shadow_enabled
    shadow.toggled.connect(func(value): world.sun.shadow_enabled = value; save_settings())
    panel.add_child(shadow)
    var effects = CheckButton.new()
    effects.text = "Short spell effects · no camera cut"
    effects.custom_minimum_size.y = 56
    effects.button_pressed = short_spell_effects
    effects.toggled.connect(func(value): short_spell_effects = value; save_settings())
    panel.add_child(effects)
    var scale_option = TideUI.option(["Render resolution · 75%","Render resolution · 100%"])
    scale_option.select(1 if get_viewport().scaling_3d_scale > .9 else 0)
    scale_option.item_selected.connect(func(index): get_viewport().scaling_3d_scale = 1.0 if index else .75; save_settings())
    panel.add_child(scale_option)
    panel.add_child(TideUI.paragraph("Frame targets still require testing on physical Android devices. Camera recenter is always available beside the movement controls.",17))
    panel.add_child(TideUI.button("Return to sign in",return_requested.emit))

func save_settings() -> void:
    var config = ConfigFile.new()
    config.load("user://settings.cfg")
    config.set_value("graphics","fps",Engine.max_fps)
    config.set_value("graphics","shadows",world.sun.shadow_enabled)
    config.set_value("accessibility","short_spell_effects",short_spell_effects)
    config.set_value("graphics","scale",get_viewport().scaling_3d_scale)
    config.save("user://settings.cfg")

func show_chat() -> void:
    var panel = hud.open_panel("Say something")
    if preview:
        panel.add_child(TideUI.paragraph("Nearby chat is available when connected to the world."))
        return
    for pair in [["hello","Hello, Wayfarer!"],["help","Could you lend a light?"],["thanks","Thank you!"],["follow","Let's explore together."],["farewell","Safe tides!"]]:
        panel.add_child(TideUI.button(pair[1],_say.bind(pair[0])))

func _say(phrase: String) -> void:
    connection.say(phrase)
    hud.close_panel()

func _refresh_auth() -> void:
    var result = await ApiClient.post_json("/auth/refresh",{})
    if not result.is_empty():
        ApiClient.access_token = result.access_token
        connection.start(character.id)

func _exit_tree() -> void:
    if connection:
        connection.stop()
    for remote in remotes.values():
        remote.avatar.queue_free()
    if is_instance_valid(player):
        player.queue_free()
    if is_instance_valid(camera):
        camera.queue_free()
