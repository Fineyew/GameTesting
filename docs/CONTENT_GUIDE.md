# Content authoring

Source of truth: `content/<category>/<stable_key>.json`. Keep keys stable, schema_version 1,
and increment definition versions when behavior changes. Use nearby existing definitions
for shape. Run `python -m tools.build_catalog` to validate and regenerate the deterministic
`godot_project/data/catalog.json`; commit source and bundle together. Run relevant tests.

| Category | Actual runtime support |
|---|---|
| Spells | Focus costs 0–6; deal_damage(power), restore_vigor(amount), bind, guard, mark |
| Enemies | Vigor and 1–12 repeating announced intents with integer power 0–30 |
| Quests | Starter acceptance, defeat_enemy progress, XP/item/currency rewards |
| Zones | Shared planar bounds, expanded rectangular blockers and interaction positions |
| Items | Names, server-owned quantities and reward grants |
| Other definitions | Validated/reference-linked examples; most are not runtime systems yet |

The catalog checks identity, references and handler names, plus selected numeric rules.
It is immutable during a running process. A new data file is not automatically obtainable
or playable: add and test an actual acquisition/interaction path before saying it works.
Generic branching dialogue, quest acceptance/conditions/objectives and folio selection
are the next content-framework work. Preserve the existing starter keys and progress.

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
