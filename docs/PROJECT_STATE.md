# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`, draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → PROJECT_STATE → ARCHITECTURE → relevant source. Main is bd98746; no merge/deployment.

## Current milestone

**M1.4 visual benchmark: implemented candidate; acceptance remains open.**
Roadmap checkpoint edec97b introduced this scope; the owner then authorized implementation.
The last fully validated code is `d9293fac518cda680cdcf21795ff49ec68b5db07`,
[run34480660769](https://github.com/Fineyew/GameTesting/actions/runs/34480660769), all three jobs successful.
A bounded final visual cleanup now addresses observed canopy/cast-camera occlusion,
regular paving and the blank shop side wall. Local art/Godot checks pass; its full CI is pending.
Do not mark M1.4 complete or start M1.5 before owner art-direction acceptance and the required
physical-phone install/online-touch/20-minute thermal baseline. Neither has been performed.

Completed history is preserved in ROADMAP/CHANGELOG:

| Milestone | Code | Handoff |
|---|---|---|
| M0 engineering | 1044f95 | 1044f95 |
| M1.1 story | 4efd3a6 | d138214 |
| M1.2 spell acquisition/folio | d0c6048 | 56370e6dd442485101824dc188d12e00aa87d3f8 |
| M1.3 vendor/equipment | de9d7a38bed6c18b396173cfd926c09c20e8159d | 3ac1f8fc69379b15594191294e6248e9911be950 |

## What works

- Godot4.5.1 modular gateway/creator, third-person movement, touch/camera, offline preview,
  network interpolation/reconnect, preset chat, inventory/search/settings and saved appearance.
- Argon2 accounts with legacy upgrade, short versioned sessions/revocation/renewal;
  server-owned WebSocket movement and HTTP progression. One process/room; cap32 is unbenchmarked.
- Persistent server-owned Tidebeat combat/intents/Focus/rewards, five authored quests,
  Mara's dialogue/investigation/three spell lessons, six obtainable spells and a 1–6 spell folio.
- Mara sells the existing Lanternkeeper Vest for 12 earned shell chits. One chest slot,
  Guard1 per incoming hit; purchase/equip/unequip/comparison/retries are authoritative and atomic.
  Equipment preserves appearance; the existing bandage listing stays unavailable until M1.5.
- JSON development and PostgreSQL aggregate adapters, migrations0001/0002, old-save defaults,
  revisions/receipts/concurrency protection. World1/story1/folio1/commerce1 and26 definitions unchanged.
- M1.4 adds eight original editable kit pieces around the Lantern Well/cart, a sample
  Wayfarer and distinct Mara with13-bone Idle/Walk/Cast rigs, shared appearance tints,
  grounded foliage/materials and styling in the existing HUD. Other areas remain blocked in.
- Confirmed Glimmer casts show anticipation/travel/impact with bounded lifetime, restored
  navigation and a saved short-effects/no-camera-cut option. VFX cannot grant damage/rewards.
- Pause/focus loss clears horizontal input/velocity; native pre-background capture settles
  before the unchanged resume threshold. Camera-only foliage is separate from movement geometry.

## Tested evidence / retained review APK

At d9293fa: **90 backend tests /30 subtests**, including8 real PostgreSQL tests and both
migrations; content/art budgets; strict Godot import/smoke; actual two-player Godot/API
account/story/folio/vendor/equipment/reconnect/Guard flow. Both normal and short cast
presentation restore navigation. Local baseline82 passed/8 PG skips/30 subtests; two
upstream deprecation warnings. Current local art/rig/geometry/VFX/pause checks also pass.

Actual desktop sample:74 draw calls,81,654 rendered primitives,15,182,467 texture bytes.
Matched before/after preview route MP4s pass at1280×720/.75/no shadows; Movie Maker30 FPS
is a capture setting, not a performance measurement. Native API35 x86_64 install, Folio,
Bag→vendor touch, movement, visible landscape resume and repeat touch all pass.

ARM64 **0.2.4/code6**,29,135,812 bytes; artifact10153789972, native10153791518,
render10153793102 (90-day CI retention). Source d9293fa; tested PR merge
`10d8557e3916485e1e15fc99b88a2d3f3f20b0c4`.
SHA256 `80f02345666bbe75da56eb7c6e8e4016a35bed137877123bd874cfc73d20eea9`.
Downloaded CRC/hash, ARM64-only libraries, version/code, v2 signature report and packaged
art/presentation scripts verified. This is the prior candidate; final visual-cleanup APK pending.

Initial b5b90a5 native resume failed at19.35% changed pixels; artifact10152976777 retained,
no ARM64 published. Inspection found a separate dropped-transform art bug. Both corrections
pass at d9293fa. Intermediate f4ef6ec failed an overconservative rotated-AABB test; it now
checks actual transformed vertices. KNOWN_ISSUES keeps failure evidence and prior M1.3 history.

## Placeholder / unverified / next

Owner art acceptance and **all physical ARM64 phone validation remain unverified**.
Two houses, distant trees/coast/vistas, dock, cistern, lurker, most spell VFX, all audio,
full animation/creator variety, wearable vest mesh and full UI/accessibility remain unfinished.
Tree canopy shapes affect cameras only; movement still uses the preserved planar catalog.
No new quests/spells/regions, consumable use, selling/trading, dungeon/co-op, gathering/crafting,
mounts/housing/pets or broad social content were added. Account recovery/moderation, load tests,
JSON→Postgres import/restore drills, production deployment/signing/updater remain future work.

Finish M1.4 validation/review first; **M1.5 is the still-unstarted Sunthread Bandage loop**.
Use README's local backend/USB reverse recipe for phone testing; a paid public server is
not required for this review. The inherited public endpoint has not been updated/verified.

## Build / continue

Install `backend/requirements.lock`; run `python -m pytest backend/tests -q`,
`python -m tools.build_catalog`, `python -m tools.check_art`. Set GODOT_BIN to4.5.1 and run
`python -m tools.check_godot` / `python -m tools.check_online`. CI supplies PG16, SDK35,
JDK17/templates and native/render gates; README documents export and matching route capture.
New art is in `art_sources`, `godot_project/assets/dawnreef`, DawnreefArt, WayfarerAvatar,
GlimmerPresentation and VisualBenchmark. CONTENT_GUIDE owns source/import/budget instructions.
Preserve service injection, catalog IDs, aggregate locks/receipts and deferred HUD deletion.
