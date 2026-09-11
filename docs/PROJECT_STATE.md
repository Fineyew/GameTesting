# Veilbound Tides — project state

Updated 2026-09-11. Branch `feature/android-foundation`, draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → PROJECT_STATE → ARCHITECTURE → relevant source. Main is bd98746; no merge/deployment.

## Current milestone

**M1.5 bandage loop: implemented; Android gate correction awaiting CI.**
The owner requested full continuation after the M1.4 device-gate handoff. Engineering
continues while physical validation remains explicitly outstanding; this is not a phone pass
or a declaration that M1.4/M1.5 acceptance is complete. M1.4 handoff a5d06db/run34484981552
passed all three CI jobs. This increment changes no public deployment, regions or art assets.

M1.5 adds one-wrap use through existing CommerceService locks/revisions/receipts, capped
12-Vigor restoration, server-owned max_vigor=30, full-health/active/unowned rejection,
shop version3 bandage availability, and Bag health/effect/use feedback. No new save fields
or migration; item_use_protocol1 is additive. Existing world/story/folio/commerce remain1.
Local:97 backend passed /9 PostgreSQL skipped /30 subtests; real Godot/API purchase/use/
reconnect passed. Candidate f761714/run34547305384 passed backend106/30 (including9 real PostgreSQL tests),
Godot/API and render71 calls/83,630 primitives. Native post-resume locomotion failed;
Android logged an undeliverable touch during its resume transition. The harness now waits
for stable app focus/ready surface state before its one swipe, with unchanged thresholds.
A review also corrected item-use failure routing so server reasons reach the Bag recovery
UI; the Godot/API gate now tests stale use, clear feedback and unchanged supplies after reload.
0edc990/run34548765608 passed backend/Godot/render; its first readiness parser failed
closed on an absent legacy Android field. Seven regression tests and the actual retained
API35 dump pass with the corrected focused/ready-surface parser. Full CI and ARM64
0.2.5/code7 remain pending; no M1.5 APK claimed yet.

**M1.4 visual benchmark remains an acceptance-open candidate.**
Roadmap checkpoint edec97b introduced this scope; the owner then authorized implementation.
Validated code checkpoint: `365993ce7e79fc29025ee23d1c77cbf449ad2bfc`,
[run 34483308643](https://github.com/Fineyew/GameTesting/actions/runs/34483308643), all three jobs successful.
Actual overview, Mara, vendor, Glimmer, native resume and matched-route frames were inspected.
The final pass clears camera foliage, grounds the paving and finishes the sample shop side.
Do not mark physical-phone install/online-touch/20-minute thermal acceptance complete without
actual measurements. Continued engineering does not substitute for that evidence.

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
  Equipment preserves appearance; the existing bandage listing is enabled by the M1.5 candidate.
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

At 365993ce: **90 backend tests / 30 subtests**, including 8 real PostgreSQL tests and both
migrations; content/art budgets; strict Godot import/smoke; actual two-player Godot/API
account/story/folio/vendor/equipment/reconnect/Guard flow. Both normal and short cast
presentation restore navigation. New smoke covers imported geometry/rig motion, single
VFX impact/cleanup, camera obstruction layers/framing and pause input reset.
Local baseline: 82 passed / 8 explicit PostgreSQL skips / 30 subtests; current headless/art
checks pass. PostgreSQL, real display/API and Android gates were executed in CI; two
upstream backend test deprecation warnings remain.

Actual desktop sample: **71 draw calls, 83,630 rendered primitives, 15,182,467 texture bytes**
within unchanged 150-call/150k/128 MiB gates. Kit: 25,638 source triangles, 2 materials;
Wayfarer: 10,538 / 4; Mara: 10,414 / 3. The three GLBs total 4,085,572 bytes.
Matched before/after preview MP4s: 925 frames each, 30.83 seconds, 1280×720/.75/no shadows.
Movie Maker 30 FPS is a capture setting, not a performance measurement. Native API35
x86_64 install, Folio, Bag→vendor touch, movement, visible landscape resume and repeat
movement pass with no engine errors (initial movement changed-world fraction 0.293).

Verified ARM64 **0.2.4/code6**, **29,144,004 bytes**; build artifact **10154911714**,
native **10154913361**, render **10154915083** (CI retention through 2026-12-09).
Source `365993ce7e79fc29025ee23d1c77cbf449ad2bfc`; tested PR merge
`38bd671a40e2f8469f9f75b680c1e38207144fd9`.
SHA256 `d5ba342559fc0a19e0bcdc6133128415dce30467ff796b2a392d7a66ae0f65ab`.
Downloaded ZIP/APK CRC/hash, ARM64-only libraries, version/code, retained v2/v3 signature
report and packaged art/presentation scripts verified. Minimum API24 / target API35.
The review APK, before/after movies and evidence bundle are retained for the owner handoff.
Signing is an ephemeral debug identity, not a production or stable update key.

Initial b5b90a5 native resume failed at19.35% changed pixels; artifact10152976777 retained,
no ARM64 published. Inspection found a separate dropped-transform art bug. Both corrections
pass at d9293fa. Intermediate f4ef6ec failed an overconservative rotated-AABB test; it now
checks actual transformed vertices. KNOWN_ISSUES keeps failure evidence and prior M1.3 history.

## Placeholder / unverified / next

Owner art acceptance and **all physical ARM64 phone validation remain unverified**.
Two houses, distant trees/coast/vistas, dock, cistern, lurker, most spell VFX, all audio,
full animation/creator variety, wearable vest mesh and full UI/accessibility remain unfinished.
Tree canopy shapes affect cameras only; movement still uses the preserved planar catalog.
No new quests/spells/regions, selling/trading, dungeon/co-op, gathering/crafting,
mounts/housing/pets or broad social content were added. Account recovery/moderation, load tests,
JSON→Postgres import/restore drills, production deployment/signing/updater remain future work.

Finish M1.5 automated validation/checkpoint, then M1.6 authoring tooling is next engineering work.
M1.4/M1.5 physical acceptance remains open; do not report it complete without device evidence.
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
