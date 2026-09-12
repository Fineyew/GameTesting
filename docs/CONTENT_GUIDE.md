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
| Items/equipment | Server-owned quantities; chest gear, Guard/comparison/equip; single-wrap capped healing |
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
M1.3 retained unavailable bandages; M1.5 enables the existing listing alongside tested item use.

Equipment currently supports only chest, required_level 1–1000, stack_limit1 and one
modifier `{stat: "guard", operation: "add", value: 0..3}`. The vest uses Guard1. Unsupported
stats/operations, malformed prices/quantities, broken references and duplicate listing
keys fail catalog validation. Other items require stack_limit 1–10000. Sell values remain
metadata; there is no sale endpoint. Models/icons named in assets are still proposed bindings.

Rules live in inventory/InventoryRules; orchestration lives in vertical_slice/CommerceService.
The server returns comparison/owned/equipped/price data from one locked aggregate snapshot.
Clients cannot grant items, send prices/stat modifiers or invent equipment ownership.
Run the complete backend/PostgreSQL, Godot/API, render and Android gates after changes.

The first vendor/equipment loop is validated at de9d7a3/run34440512749. Preserve the
native Bag→vendor touch gate when changing navigation; invoking a button signal alone
does not exercise Android input dispatch and previously missed a panel lifecycle error.

## M1.4 editable art and imports

Use Blender **4.5.3 LTS** for the sample recipes; the runtime remains Godot4.5.1.
Open `art_sources/dawnreef/*.blend` for direct mesh/rig edits, or regenerate the original
sample geometry/vertex palette/animation from the recipes (regeneration overwrites edits):

```bash
blender --background --factory-startup --threads 2 --python art_sources/build_dawnreef.py
blender --background --factory-startup --threads 2 --python art_sources/build_wayfarer.py
python -m tools.check_art
python -m tools.check_godot
```

Recipes use metres, Godot Y-up/-Z-forward, converted to Blender coordinates for export.
Export self-contained GLBs with vertex colors and named animation clips. Keep the editable
source and recipe; commit `.glb.import` so LOD/import settings stay reviewable. No Blender
installation is required for ordinary game CI. Follow Godot's
[glTF import guidance](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_3d_scenes/available_formats.html).

`art_sources/dawnreef/manifest.json` records candidates, source paths, provenance, budgets
and remaining placeholders. `DawnreefArt` maps named kit pieces to placements. No gameplay
content/catalog IDs changed; existing proposed model/icon bindings elsewhere are not
implemented by this sample. Appearance tint slots are `RobeTint` and `SkinTint`; common
accessories use shared materials. Keep 13 rig bones and Idle/Walk/Cast clips until an
explicit compatible rig migration. Do not introduce client-only movement colliders or
terrain. Camera-only foliage uses layer2 and is excluded from the player layer1 mask;
validate that separation. Preserve imported node transforms when batching the kit; test
actual transformed vertices for oriented extents, not a re-transformed enclosing AABB.

The strict smoke test samples actual imported bone motion, a single VFX impact/cleanup,
then records gameplay/benchmark/Mara/Wayfarer/Glimmer frames under a real display. The
existing online gate still earns/casts/buys through the real API. A screenshot fixture
cannot stand in for progression, a walkthrough review or physical-phone measurement.

`xvfb-run -a python -m tools.record_benchmark` records matching before/after MP4 routes
from M1.3 de9d7a3 and current source with pinned camera/control/.75/no-shadow settings.
It requires FFmpeg and may fetch the named baseline into Git; it extracts to a temporary
project and never switches the working branch. These are offline Movie Maker captures,
not real-time benchmarks. Source provenance is retained beside the recordings.

## M1.5 restorative items

An item may declare one use_effects entry with type restore_vigor and integer amount1–30.
Unknown effects, extra effect fields, bool/noninteger amounts and multiple effects fail
validation. Items without use_effects remain nonusable resources. Sunthread Bandage keeps
its existing12-point effect/20 stack cap; shop version3 enables its existing five-chit listing.
Increment shop version whenever changing a quote/availability; never change stable item IDs.
Item use consumes exactly one after ownership, inactive combat and missing-Vigor validation.
No client-supplied quantity/heal values, consumable stat rolls or combat consumables exist.

## M1.6 authoring workflow

Keep production definitions in `content/`; generated catalogs remain disposable snapshots.
These tools extend the existing catalog/rules, not a parallel CMS or live publication API:

```bash
python -m tools.author_content check
python -m tools.author_content example --output /tmp/veilbound-authoring-example
python -m tools.author_content check --content-root /tmp/veilbound-authoring-example/content
python -m tools.build_catalog --content-root /tmp/veilbound-authoring-example/content --output /tmp/example-catalog.json
python -m tools.author_content encounter --actions gather,glimmer_spark --folio glimmer_spark,root_snare,tide_mend
python -m tools.check_authoring
# Interactive desktop/editor preview, with temporary account/client data:
python -m tools.check_authoring --content-root /tmp/veilbound-authoring-example/content --interactive
```

Choose a new example output directory. The tool refuses existing output and nested source
workspaces. It copies all original definitions unchanged except a versioned Mara offer and
branch, and adds one tiny listen-to-reeds/return-to-Mara quest with an earned five-XP reward.
Edit its JSON in any editor. It never inserts this example into the production catalog.
The example manifest records original checksums. Commit your authored workspace/content
changes when ready; rollback by restoring the prior versioned definitions and rebuilding
the bundle. Do not rollback a live reward definition blindly after players have earned it.

The automated preview creates its own catalog/client copy, local API, random signing key,
JSON save and client settings. It earns the example through actual movement/dialogue/
landmark/talk actions and verifies the once-only reward/save. All temporary accounts and
settings are discarded at exit. Interactive preview uses the same isolation but waits for
the author to create a test account; the production endpoint/save is never selected.
The default automated scenario expects the generated `authoring_echo` example. A custom
catalog needs its own authored integration scenario, not debug grants. These scripts are
under Godot's existing `tests/*` Android export exclusion.

`authoring/bindings.json` inventories all declared asset paths and existing interaction
bindings. Missing/unbuilt paths must remain `planned` with a reason. Existing placeholders
are not final; a candidate needs a file, editable source and license/provenance. `final`
requires an acceptance record matching the actual SHA256 with a named reviewer and existing
visual/device evidence paths. This validates evidence references, not the truth or quality
of an artist's claim: actual review/phone validation is still required. No assets are marked
final by this milestone. The existing art manifest remains the source for kit/rig budgets.

Interaction bindings point to existing scene, world construction and dispatch source;
the doctor checks them against zone/NPC/enemy/discovery content. Metadata alone cannot
spawn a new NPC or implement a new interaction. Additional runtime placements/handlers
must be integrated and exercised through a Godot/API scenario. Unsupported executable
quest objectives and structurally unreachable dialogue branches fail. Conditional branch
reachability still needs authored scenarios; a static graph walk cannot prove every story.

Continue the M1.4 metre/Y-up/-Z-forward, grounded pivot, named tint/rig/animation and
self-contained GLB conventions. Keep source recipes/import settings and generated LODs.
The current vertex-color kit uses no texture atlas; a future textured kit must record its
atlas resolution/material/texture budget and validate imports/rendering before acceptance.
Run `tools.check_art`, strict Godot checks and the next playable render/device gates after
any asset export. This workflow does not make missing assets or proposed systems playable.

## World geometry authoring guard (M1.7 groundwork)

The catalog now validates `rules.world` before references are traversed. Bounds are four
finite coordinates within±512m, ordered with at least2m per axis. Spawn is a finite x/z
pair with0.35m capsule clearance from bounds/blockers. Up to128 ordered blockers must
lie inside bounds; up to128 named interactions have finite in-bounds x/z coordinates.
Speed is0.1–12m/s, acceleration/deceleration0.1–64m/s²; omitted parameters retain runtime
defaults. Radius is0.35 to match the current client. Boolean/NaN/infinite/oversized values,
malformed shapes and unknown fields fail before runtime, including unsupported terrain.
These bounds are validation limits, not tested performance capacity or permission to
expand the hardcoded Dawnreef scene. A scene must still implement its catalog geometry.
The live catalog/bundle is unchanged. Follow ARCHITECTURE's planned M1.7 terrain contract
only when the Python/Godot implementation and versioned handshake are ready together.

## M1.7 isolated terrain contract

`TerrainSurface` in the existing Python world module and Godot world scripts accepts
`{"bounds":[-2,-2,2,2],"cells":{"0:0":[0,0,300,300]}}`. Bounds are integer-valued
metres (absolute limit4096), with1–128 cells per axis. Keys are canonical nonnegative
`x:z` indices relative to the minimum bounds. Missing cells are flat zero. Heights are
integer-valued millimetres within±8000, SW/SE/NE/NW. Both runtimes accept integral JSON
numbers and reject booleans/fractions/extra fields. SW→NE is the fixed triangle diagonal;
interior edges belong to the positive-axis cell, outer maxima to the final cell.

This is a fixture-only contract: the live catalog deliberately still rejects terrain.
Run `python -m tools.check_terrain` after Godot import to compare shared analytic/seeded
queries and actual collision rays. Do not activate these surfaces as walkable content
until capsule sweeps, protocol2 negotiation/reconciliation and old-save checks pass.

## Fal candidate assets (not runtime-approved)

The first generated lantern and two sounds are preserved under
`art_sources/candidates/fal_dawnreef_20260912`, outside the exported Godot project.
The folder records prompts, settings, request IDs, hashes and technical checks.
These are experimental candidates, not replacements for accepted assets or claims of
commercial-license verification. Do not put them in the final-art manifest yet.

Lantern:2,421 triangles,1 material, three2K textures; evaluate512/1024px derivatives,
scale/pivot, emissive core and mobile budget before integration. Sound sources are
3s/20s stereo MP3; a separate spell WAV has3dB attenuation to avoid decoded full-scale
overs. Listening, seamless looping and in-game mix remain unverified. Preserve originals.
Use the lantern in a future Dawnreef visual pass only after Godot/device checks; audio
follows M1.9's buses/volume/lifecycle framework. No further paid generation is needed now.

## Live terrain authoring (M1.7 activation)

Dawnreef version4 activates `rules.world.terrain` and `geometry_revision: 2`. Reuse the
core terrain schema: integer metre bounds, sparse `x:z` cell indices relative to bounds,
SW/SE/NE/NW millimetre heights and deterministic SW–NE diagonal. Omitted cells are flat.
All geometry numbers must be millimetre-precision. Keep terrain bounds equal to world bounds
and elevation at least4m from existing spawn/interactions. Preserve existing definition IDs.

Run catalog/authoring checks, backend tests and `python -m tools.check_terrain`; a catalog
change alone is insufficient. Traversability checks entire touched cells and edge endpoints
against42°/.3m, with .35m enclosing square clearance. Leave generous route/turning width.
Mooring Rise is4m wide at x4..8,z10..18; ramp peaks1.2m. The ground path bounds derive
from sparse cells, and surface triangles generate mesh and collision. Add separate visual
review for new shapes; the sparse-cell bounding rectangle is only this route’s paint mask.

Changes alter the negotiated geometry digest and require a matching client/backend release.
No author may grant altitude through a save or movement message. Use the isolated preview
workflow, online route tests and render budgets before exporting. Do not add broad terrain
content before the route’s outstanding physical/feel review.
