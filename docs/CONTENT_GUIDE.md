# Content authoring

Source of truth: `content/<category>/<stable_key>.json`. Keep keys stable, schema_version 1,
and increment definition versions when behavior changes. Use nearby existing definitions
for shape. Run `python -m tools.build_catalog` to validate and regenerate the deterministic
`godot_project/data/catalog.json`; commit source and bundle together. Run relevant tests.

| Category | Actual runtime support |
|---|---|
| Spells | Focus costs 0–6; deal_damage(power), restore_vigor(amount), bind, guard, mark |
| Enemies | Vigor and 1–12 repeating announced intents with integer power 0–30 |
| Quests | NPC offers, level/quest conditions, ordered defeat/inspect/talk/cast objectives, XP/item/currency/spell rewards |
| Dialogue | Conditional entry nodes, options/branches, quest offers and server-owned cursor validation |
| Zones | Shared planar bounds, expanded rectangular blockers and interaction positions |
| Items/equipment | Server-owned quantities; chest gear, additive Guard, comparison/equip |
| Shops | NPC-proximity purchases at catalog prices, availability and stack limits |
| Other definitions | Validated/reference-linked examples; most are not runtime systems yet |

The catalog checks identity, references and handler names, plus selected numeric rules.
It is immutable during a running process. A new data file is not automatically obtainable
or playable: add and test an actual acquisition/interaction path before saying it works.
The narrow dialogue/quest framework and server-owned folio selection are implemented. Broader objective types
remain future work. The catalog currently has 26 definitions, including five playable quests. Preserve existing starter/objective keys and progress.

The combat engine receives a catalog port; `vertical_slice/encounters.py` commits quest,
inventory, XP, wallet and command receipts in one store transaction. Never grant rewards
or declare quest completion from client UI. Keep gameplay modules independent through
injected ports and shared contracts, as enforced by module-boundary tests.

The current world uses `ReefKit` and reusable Godot avatar/world scripts. Static meshes
are merged by material; animated objects remain separate. Replace placeholder assets
with modular scenes/GLB resources as art is authored. Many early content asset paths are
proposed bindings to files that do not yet exist; the paths are not finished assets.

When editing zone geometry, regenerate the bundle and ship matching client/server data.
Startup rejects geometry mismatches. Server x/z are meters, radius .35 m, speed 4.8 m/s,
acceleration 16 and deceleration 24. Authored slopes/stairs need shared vertical authority
before extending the flat region. Do not add invisible client-only movement shortcuts.

## Authoring a playable conversation/investigation

Use `mara_first_meeting.json` and `an_answer_in_the_reeds.json` as the tested shapes.
A dialogue has start_node, optional ordered entry_nodes with conditions, and at most 32
nodes. Nodes contain text and up to 8 uniquely keyed options; next_node branches and
`offer_quest` is the only permitted effect. Direct item/currency/XP grants in dialogue
are rejected. Add an offered quest to its giver NPC's available_quests; the quest's
giver_npc_key must match. No new server rule handler is needed for another conversation in this shape. Additional
NPC visual placement/interaction bindings still require scene authoring; this increment
makes story rules data-driven, not automatic world construction.

Conditions: character_level_at_least(value), quest_completed(quest_key), and
quest_state(quest_key,state=not_started/accepted/completed). All conditions are ANDed.
Entry nodes are evaluated in authored order; first match wins, otherwise start_node.
The server chooses nodes and reevaluates option conditions; clients submit option keys.

Objectives: defeat_enemy(enemy_key,quantity), inspect_landmark(zone_key,interaction_key,
quantity=1), talk_to_npc(npc_key,quantity=1). Each needs a unique stable key and optional
label for HUD/journal. `ordered:true` advances only the first unfinished objective.
Zone rules.discoveries maps existing world interaction keys to title/text; the API
requires live proximity. Defeat events come from combat, never client declarations.
collect_item remains a reserved definition type; accepting such a quest is rejected
until a real inventory-event handler exists. Repeated/repeatable quests are not supported.

Quest rewards allow only grant_experience(amount), grant_currency(currency_key,amount),
grant_item(item_key,quantity), and learn_spell(spell_key). Numeric rewards require positive
integers up to 10000 per entry. learn_spell accepts only type/spell_key, requires an existing
spell definition, and adds ownership once; it never auto-prepares a spell. Objectives
cap at 1000; discovery/talk quantities must be 1. The validator rejects negative/bool
quantities, broken references/branches, malformed rule lists and direct dialogue rewards.
Run catalog generation, backend tests and the actual Godot/API check after changes.

## Spell lessons and folio authoring

Use reading_the_afterlight, what_the_reeds_hold and a_measured_release as acquisition
examples. Preserve the original two quests and their reward flags; do not append a reward
to a completed quest expecting old characters to receive it. Add a gated continuation so
existing M1.1 characters can earn new spells without resetting progress. Dialogue still
only offers quests; learn_spell is forbidden as a direct conversation effect. The Folio
shows acquisition hints by reading quest rewards, without another source mapping.

cast_spell objectives require spell_key and quantity; optional enemy_key and
intent_power_at_least (integer 0–30) constrain the target and announced response.
Only a successful server combat resolution emits this event, within the cast/reward
transaction. Rejected casts and repeated receipt replays emit nothing. Ordered objectives
retain their order, including a subsequent defeat_enemy and talk_to_npc turn-in. There is
no client endpoint for declaring a cast or learning a spell. The compatibility one-shot
fight does not provide practice credit.

Folio capacity is six server-owned slots; 1–6 unique known spell keys are required.
Brace/Gather are universal actions, not spell definitions or selectable slots. Future
spells need working effects and acquisition before inclusion; do not add new families
merely to populate the collection. Run backend/PostgreSQL, Godot online, render and native
Android gates after altering preparation or acquisition behavior.

## Dawnreef supplies and equipment

M1.3 activates existing `shops/dawnreef_supply_cart` and `equipment/lanternkeeper_vest`;
there are still 26 definitions. Increment versions when listings/prices/rules change.
Do not change stable listing/item keys to fix display text. Items and equipment keys
must not collide because the existing inventory map uses item keys across both categories.

A shop declares `npc_key` and `zone_key`. The NPC must point back through `shop_key` and
have an existing world interaction. Each of 1–16 listings has a unique key, item_key,
quantity (bundle size 1–100), explicit boolean available and exactly one shell_chits price
(integer 1–10000). Unavailable listings require unavailable_reason. The client requests
1–10 bundles; the server multiplies price/count and checks the stack limit under lock.
The current vest bundle is one and its stack_limit is one; quantity2 is rejected.
The retained bandage listing is unavailable. Do not enable it before item use is playable.

Equipment currently supports only chest, required_level 1–1000, stack_limit1 and one
modifier `{stat: "guard", operation: "add", value: 0..3}`. The vest uses Guard1. Unsupported
stats/operations, malformed prices/quantities, broken references and duplicate listing
keys fail catalog validation. Other items require stack_limit 1–10000. Sell values remain
metadata; there is no sale endpoint. Models/icons named in assets are still proposed bindings.

Rules live in inventory/InventoryRules; orchestration lives in vertical_slice/CommerceService.
The server returns comparison/owned/equipped/price data from one locked aggregate snapshot.
Clients cannot grant items, send prices/stat modifiers or invent equipment ownership.
Run the complete backend/PostgreSQL, Godot/API, render and Android gates after changes.
