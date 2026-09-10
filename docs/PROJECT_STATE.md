# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`; draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → this file → ARCHITECTURE → relevant source before editing.

## Current checkpoint

**M1.3 complete.** Code/APK source `de9d7a38bed6c18b396173cfd926c09c20e8159d` passes all
required gates in [run34440512749](https://github.com/Fineyew/GameTesting/actions/runs/34440512749).
M0 remains complete at1044f95; M1.1 at4efd3a6/d138214; M1.2 atd0c6048/56370e6. The M1.2
handoff run34437584787 also passed all jobs. Main remains bd98746; no merge or deployment.
Preserve original IDs, accounts/saves and all working systems.

**M1.4 benchmark candidate is in progress** after roadmap checkpoint
`edec97b128cf8cd86ca2c788ebe737316c71742d` (run34463841938 passed).
The owner authorized implementation on this branch. Original editable GLBs/Blender sources
now replace the small well/cart area, one Wayfarer and Mara; imported idle/walk/cast,
Glimmer presentation, ground/contact shading and existing HUD styling are integrated.
Headless Godot/import/rig/VFX smoke and art budgets pass locally. Full current CI, actual
render inspection and Android0.2.4/code6 validation are pending. No M1.4 APK is verified yet.
Owner art-direction acceptance and real-phone thermal/touch validation remain open; do
not mark M1.4 complete or begin M1.5 until its roadmap gate is satisfied.

## What works

- Modular Godot4.5.1 gateway/creator, appearance/affinity, third-person movement, camera,
  touch controls, procedural Dawnreef, search/settings and explicit offline preview.
- Argon2 accounts, legacy hash upgrade, versioned access sessions/revocation/renewal.
- Server-owned WebSocket movement/presence/interpolation/reconnect and preset chat.
  World protocol1 unchanged; one process/room, 32-player cap still unbenchmarked.
- Persistent Tidebeat intents/Focus/turns, prepared spells and atomic/retry-safe rewards.
- M1.1 catalog dialogue, persisted cursors, NPC offers and ordered objectives; M1.2 Mara
  investigation/three lessons. Five playable quests, one enemy, six obtainable spells,
  persistent 1–6 spell folio with ownership/revision/retry protection and combat locks.
- JSON development and PostgreSQL aggregate adapters; existing migrations0001/0002.
- **M1.3:** Mara's existing supply cart sells the Lanternkeeper Vest for 12 earned shell
  chits. One owned copy, one chest slot. Catalog Guard1 reduces each incoming hit by one,
  adds to Brace/spell protection and leaves robe appearance, Focus and spells unchanged.
- Atomic spend/grant, server prices/availability/level/stack/slot validation, explicit
  equip/unequip, commerce revision and existing receipts. Active combat blocks changes;
  new buys require live proximity to Mara. Matching retries can replay after leaving.
- Touch Bag/vendor panels in the existing HUD: currency, prices, owned/equipped state,
  Guard comparison, search, saved feedback and exact-command retry/reload. No preview writes.
- Still 26 catalog definitions; existing item/vendor/listing keys preserved. Bandages are
  visible but unavailable to buy until item use works. No other content increment started.
- Old saves default commerce_revision0/missing equipment; no DDL or reset. Old encounters
  without equipment_guard resolve with zero gear bonus. Client0.2.3 requires commerce1
  alongside world1/story1/folio1; inventory module status now reflects its narrow rules.

## Tested evidence and retained APK

At **de9d7a3**, all three CI jobs passed on the first attempt: **90 backend tests and
30 subtests**, including eight real PostgreSQL tests and both migrations. Coverage includes
forged prices/items/stats, insufficient funds, retries/conflicts/stale revisions, concurrent
spending across independent connections, rollback after SQL writes, equipment legality/
active-combat locks and old JSON/JSONB saves. Local: 82 passed, eight PostgreSQL tests
explicitly skipped, 30 subtests; two upstream test deprecation warnings remain.

Godot import/smoke and full real Godot/API progression passed: account/creator, two-player
presence, original story, all spell lessons/folio/reconnect/earned Lance, then purchase
with earned chits, comparison, equip/unequip/reconnect and Guard combat. Folio/appearance
remain unchanged. Smoke additionally dispatches GUI mouse input; every Godot gate rejects
engine errors. The native gate supplies actual Android touch input.

ARM64 debug APK **0.2.3/code5**, **27,914,052 bytes**, minimumAPI24/target35.
Artifact **10137878626**, runtime evidence **10137878970**, retained until2026-12-09.
Manifest source de9d7a3; tested PR merge commit `27f320efeca82be2af58013f8797836014c1636d`.
SHA256: `cd4c196dc7d679f6c64aa978f8c16fb08a7e2a8c1ec03c5ba5d9e34bdec568fb`.
Downloaded bytes/hash, ARM64-only libraries, version/code/signature report, compiled
CommercePanel and shop catalog verified. APK retained for owner handoff.

API35 x86_64 emulator: install, visible gateway, Folio open/close, Bag→vendor touch,
locomotion, background/resume to a visible landscape world and repeat movement pass.
Desktop vendor/equipment and native vendor/resumed frames inspected. **89 draw calls**
(default desktop scene; budget150). Native coverage is preview/navigation/resume;
online transactions are tested through the real Godot/API flow, not a physical phone.

Initial candidate19ac379 had two native failures: a Pixel Launcher ANR overlay, then a
real can_process error from detaching a panel during touch dispatch. The HUD now hides
retiring controls and queues deletion; fresh full CI validates the fix atde9d7a3. Failure
artifacts10137449675/10137587989 remain recorded in KNOWN_ISSUES. No thresholds weakened.

## Placeholder / unverified / planned

Physical S25 Ultra/ARM64 install/touch/safe areas, sustained FPS/thermal/memory/battery
and cellular/Wi-Fi transitions remain **unverified release gates**. Public backend not
updated/verified; use this branch's backend. Release signing/store publication unfinished.
README gives local-server/USB reverse and physical-device procedures.

Procedural art, gait/VFX, flat terrain and cart/vest asset bindings remain placeholders;
no finished wearable vest mesh or audio. No full cosmetic override/transmog system.
Item use/selling/trading, additional gear, gathering/crafting, mounts/housing/pets,
dungeon/boss/co-op, free chat/moderation and account recovery remain unfinished.
JSON→PostgreSQL import, backup/restore drills and load tests remain release gates.
Intermittent emulator/launcher startup reliability remains open in KNOWN_ISSUES.

## Next / build and test

**Stop at M1.3.** Recommended narrow M1.4: server-owned out-of-combat Sunthread Bandage
use with capped healing, atomic consumption/retries and clear Vigor UI; enable its existing
shop listing only once functional. No bulk content or new regions/families/dungeon/crafting.

`python -m pip install -r backend/requirements.lock`; `python -m pytest backend/tests -q`;
`python -m tools.build_catalog`. Set GODOT_BIN to4.5.1; run `python -m tools.check_godot`
and `python -m tools.check_online`. CI supplies PostgreSQL16, SDK35/JDK17/templates.
README covers export/render/emulator and physical-device commands. Key additions:
inventory/rules.py, vertical_slice/commerce.py, test_commerce.py, ui/commerce_panel.gd.
Preserve composition-root injection, aggregate locks and the deferred HUD lifecycle.
