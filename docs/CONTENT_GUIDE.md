# Content authoring

Source of truth: `content/<category>/<stable_key>.json`. Keep keys stable, schema_version 1,
and increment definition versions when behavior changes. Use nearby existing definitions
for shape. Run `python -m tools.build_catalog` to validate and regenerate the deterministic
`godot_project/data/catalog.json`; commit source and bundle together. Run relevant tests.

| Category | Actual runtime support |
|---|---|
| Spells | Focus costs 0–6; deal_damage(power), restore_vigor(amount), bind, guard, mark |
| Enemies | Vigor and 1–12 repeating announced intents with integer power 0–30 |
| Quests | NPC offers, level/quest conditions, ordered defeat/inspect/talk objectives, XP/item/currency rewards |
| Dialogue | Conditional entry nodes, options/branches, quest offers and server-owned cursor validation |
| Zones | Shared planar bounds, expanded rectangular blockers and interaction positions |
| Items | Names, server-owned quantities and reward grants |
| Other definitions | Validated/reference-linked examples; most are not runtime systems yet |

The catalog checks identity, references and handler names, plus selected numeric rules.
It is immutable during a running process. A new data file is not automatically obtainable
or playable: add and test an actual acquisition/interaction path before saying it works.
The narrow dialogue/quest framework is implemented; folio selection and additional objective
types remain next work. Preserve existing starter/objective keys and progress.

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
A dialogue has start_node, optional ordered entry_nodes with conditions, and at most32
nodes. Nodes contain text and up to8 uniquely keyed options; next_node branches and
`offer_quest` is the only permitted effect. Direct item/currency/XP grants in dialogue
are rejected. Add an offered quest to its giver NPC's available_quests; the quest's
giver_npc_key must match. No new handler is needed for another conversation in this shape.

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
and grant_item(item_key,quantity), positive integers up to10000 per entry. Objectives
cap at1000; discovery/talk quantities must be1. The validator rejects negative/bool
quantities, broken references/branches, malformed rule lists and direct dialogue rewards.
Run catalog generation, backend tests and the actual Godot/API check after changes.
