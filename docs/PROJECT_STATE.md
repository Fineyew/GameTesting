# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`; draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → this file → ARCHITECTURE → relevant source before editing.

## Current checkpoint

**M1.3 implemented; complete CI/artifact validation pending.** This candidate extends
M1.2 code d0c6048/handoff56370e6. The latter's run34437584787 is now verified successful
in all three jobs. M0 remains complete at1044f95; M1.1 at4efd3a6/d138214. Main remains
bd98746. No merge or public deployment; preserve original IDs and all existing systems.

## What works

- Modular Godot4.5.1 gateway/creator, appearance/affinity, third-person movement, camera,
  touch controls, procedural Dawnreef, search/settings and explicit offline preview.
- Argon2 accounts, legacy hash upgrade, versioned access sessions/revocation/renewal.
- Server-owned WebSocket movement/presence/interpolation/reconnect and preset chat.
  World protocol1 unchanged; one process/room, 32-player cap still unbenchmarked.
- Persistent Tidebeat intents/Focus/turns, prepared spells and atomic/retry-safe rewards.
- M1.1 catalog dialogue, persisted cursor, NPC quest offers and ordered objectives.
- M1.2 Mara investigation and three lessons; five playable quests, one enemy, six
  obtainable spells and 1–6 prepared folio. Ownership/revision/retry and combat locks.
- JSON development and PostgreSQL aggregate adapters; existing migrations0001/0002.
- **M1.3:** Mara's existing supply cart sells the Lanternkeeper Vest for12 earned shell
  chits. One owned copy, one chest slot. Server Guard1 reduces each incoming hit by one,
  adds to Brace/spell protection and never changes robe appearance or spell mechanics.
- Atomic spend/grant, catalog prices/stock/level/stack validation, explicit equip/unequip,
  persistent commerce revision and existing receipts. Combat blocks purchases/equipment
  changes; new buys require live proximity to Mara. Matching retries can replay elsewhere.
- Touch Bag/vendor panels inside the existing HUD: current chits/price/ownership/equipment,
  Guard comparison, search, feedback, exact-request retry or reload. Preview cannot transact.
- Existing item/vendor keys retained; still26 catalog definitions. Bandage listing stays
  visible but unavailable until item use works. No other content increment was started.
- Old saves default commerce_revision0 and missing equipment to empty; no DDL/reset.
  Encounter snapshots without equipment_guard resolve with zero gear bonus. New client
  0.2.3 requires commerce1 alongside world1/story1/folio1 before sign-in.

## Current validation

Local candidate: **82 tests passed, 8 PostgreSQL tests explicitly skipped, 30 subtests**;
2 upstream test deprecation warnings. Catalog validation/bundle, Godot import/smoke and
full real Godot/API flow pass. The latter retains all M1.1/M1.2 progression and proves
quest-earned vendor purchase, comparison, equip/unequip/reconnect and Guard in combat.
New regression tests cover malformed/forged buys, insufficient funds, retries/conflicts,
concurrent spending, rollback, ownership/level/active combat, JSON/JSONB compatibility.

**Pending:** complete CI PostgreSQL (including cross-connection purchases and SQL rollback),
render evidence review and Android install/Folio/Bag→vendor/touch/visible-resume gate.
Candidate Android version0.2.3/code5; no new APK claimed until required gates pass.
CI only publishes ARM64 after backend/Godot/render/native validation succeeds.

Previous tested M1.2 artifact: ARM64 0.2.2/code4, source d0c6048, run34437004626,
artifact10136657783/runtime10136658341, 27,905,691 bytes, minAPI24/target35.
SHA256 `50673c6c7d9d10d7e8ae234b404ad0257787305898c7f114267c5890b6a371c2`.
This is prior milestone evidence, not the M1.3 candidate. CHANGELOG/history retain M0/M1.1.

## Placeholder / unverified / planned

Physical S25 Ultra/ARM64 install/touch/safe areas, sustained FPS/thermal/memory/battery
and cellular/Wi-Fi transitions remain **unverified release gates**. Public backend not
updated/verified; use this branch's backend. Release signing/store publication unfinished.
README gives local-server/USB reverse and physical-device procedures.

Procedural art, gait/VFX, flat terrain, supply-cart/vest asset bindings remain placeholders;
no finished wearable vest mesh or audio. No full cosmetic override/transmog system.
Item use/selling/trading, additional gear, gathering/crafting, mounts/housing/pets,
dungeon/boss/co-op, free chat/moderation and account recovery remain unfinished.
JSON→PostgreSQL import, backup/restore drills and load tests remain release gates.
Intermittent emulator startup failure remains documented in KNOWN_ISSUES; full logs/final
frames retained. Fixed landscape and presented-HUD checks remain unchanged.

## Next / build and test

Finish M1.3 CI/artifact/documentation checkpoint, then **stop before M1.4**. Recommended
next small scope: server-owned out-of-combat Sunthread Bandage use (capped healing,
atomic consumption/retries, clear Vigor UI), then enable its existing shop listing.
No bulk content, additional families/regions, crafting/gathering or dungeon generation.

`python -m pip install -r backend/requirements.lock`; `python -m pytest backend/tests -q`;
`python -m tools.build_catalog`. Set GODOT_BIN to4.5.1 and run `python -m tools.check_godot`
and `python -m tools.check_online`. CI supplies migrated PostgreSQL16, SDK35/JDK17/templates.
README covers export/render/emulator and physical-device commands.
Key additions: inventory/rules.py, vertical_slice/commerce.py, test_commerce.py,
scripts/ui/commerce_panel.gd. Preserve composition-root injection and aggregate locks.
