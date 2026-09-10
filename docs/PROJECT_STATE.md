# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`; draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → this file → ARCHITECTURE → relevant source before editing.

## Current checkpoint

**M1.2 complete**, code/APK source `40fcfa7addaac98cd7f69329f38eb382d5c1d6dc`.
Later handoffs update documentation and Android test diagnostics only; game/APK code is unchanged. M0 completed at 1044f95; M1.1 code 4efd3a6,
handoff d138214. Main remains at bd98746; no merge or deployment. Restoration is finished.
Continue the existing architecture and IDs; do not recreate systems from conversation memory.

## What works

- Godot 4.5.1 modular gateway/creator, appearance/affinity, third-person movement, orbit/
  collision camera, touch controls, procedural Dawnreef, bag search and graphics settings.
- Argon2 accounts, legacy hash upgrade and versioned access sessions/revocation/renewal.
- Server-owned WebSocket movement/presence, interpolation/reconnect and preset chat.
  One process/room, 32-player cap unbenchmarked. World protocol 1 remains unchanged.
- Persistent Tidebeat encounters, visible intents, Focus and atomic/retry-safe combat rewards.
- JSON development and PostgreSQL adapters; migrations 0001/0002 preserve original tables.
- M1.1 catalog dialogue/branches/conditions, persisted server cursors, NPC quest offers,
  ordered defeat/inspect/talk objectives, proximity checks and once-only economic rewards.
- **M1.2:** three short Mara lessons after An Answer in the Reeds. Inspect the sealed cistern
  and return for Beacon Trace; study reeds and return for Reed Aegis; demonstrate Trace,
  Aegis against a 10-damage intent, finish the lurker encounter and return for Seam Lance.
  Five playable quests, one enemy, six obtainable functioning spells; 26 catalog definitions.
- Persistent folio: 1–6 distinct learned spells; Brace/Gather use no slots. New spells are
  learned without auto-preparation. Server validates ownership/catalog/revision and blocks
  edits in combat. Matching retries replay receipts; stale writes cannot replace newer folios.
- Touch Folio panel with learned/prepared/unavailable states, costs/effects/source hints,
  unsaved draft and retry/reload recovery. Encounters and the legacy fight enforce preparation.
- Old JSON/JSONB saves initialize folio from already-owned spells, preserving IDs/progress/
  active encounters. New optional fields need no DDL. Server-info advertises story1/folio1;
  client 0.2.2 checks both before login. README explains the required backend update.

## Tested evidence and Android artifact

[CI run 34434861638](https://github.com/Fineyew/GameTesting/actions/runs/34434861638), code 40fcfa7:
**all three jobs passed**. 59 backend tests and 30 subtests; five real PostgreSQL tests and
both migrations. Tests cover forged/unowned/duplicate folios, stale/retried/concurrent
updates, rollback, old JSON/JSONB saves, prepared-only combat and once-only spell acquisition.
Local: 54 passed, five PostgreSQL tests explicitly skipped, 30 subtests; two upstream warnings.

Godot import/smoke and full real client/API integration passed: account/creator, two-player
presence, original dialogue/investigation, all three lessons, folio UI selection/save,
reconnect, learned-but-unprepared rejection and an earned Seam Lance cast. Native Android
coverage is touch exploration/folio preview and resume; online progression uses Godot/API.

Signed ARM64 debug APK **0.2.2/code 4**, 27,905,691 bytes, minimum API24/target35.
Artifact **10135899991**, runtime evidence **10135900260**, retained until 2026-12-09.
Manifest source 40fcfa7; tested PR merge tree 2fc358a74b029508d60734549d8c8b6e3e3799a1.
SHA-256: `7c5dae35c624faa21ad4e5baf4bc05ef442f583f1dd72c2bc0fbf98802fafd3f`.
Downloaded APK hash/manifest/ABI/version, included lesson catalog and compiled Folio checked.

API35 x86_64 emulator: install, visible gateway, touch Folio open/close, locomotion,
background/resume to a landscape visible world and repeat touch movement passed. Desktop
and native Folio/resume screenshots inspected; no engine/render errors. **89 draw calls**
in the default desktop scene (150 budget), shadows off. Physical phone remains unverified.
The d138214 docs-only rerun caught a portrait launcher-transition screenshot; the gate now
waits for landscape before applying the unchanged view-match threshold and repeat touch.
Documentation checkpoint 8105f4a also passed all jobs in run 34435465708 after one Android
startup failure and an isolated retry. Its underlying cause is unverified; KNOWN_ISSUES
records it. The test now retains full system logcat and a final frame for diagnosis.
Earlier M0/M1.1 evidence remains in history/CHANGELOG; source and saves are preserved.

## Unverified / placeholder / planned

Physical S25 Ultra/ARM64 install/touch/safe areas, sustained FPS/thermal/memory/battery and
cellular/Wi-Fi transitions remain **unverified release gates**. The updated public host is
not deployed/verified; online play requires this branch's backend. No release signing.
README gives local-server/USB reverse and physical-device procedures.

Procedural art, simple gait/VFX and flat terrain are placeholders; no finished audio.
Equipment/vendors, harvesting/crafting, mounts, housing, pets, dungeon/boss, co-op combat,
free chat/moderation and full account recovery/refresh lifecycle remain unfinished.
Collect-item/repeatable quests and additional NPC visual bindings remain future work.
JSON→PostgreSQL import, backup/restore drills and load tests remain release gates.

## Next / build and test

**Stop at M1.2.** Recommended narrow M1.3: one existing Dawnreef vendor/equipment loop with
server-owned purchases/equipping, comparison and atomic/retry-safe currency/inventory.
No bulk quest/spell/world generation. ROADMAP describes the boundary.

`python -m pip install -r backend/requirements.lock`; `python -m pytest backend/tests -q`;
`python -m tools.build_catalog`. Set GODOT_BIN to 4.5.1; run `python -m tools.check_godot`
and `python -m tools.check_online`. CI provides migrated PostgreSQL and Android SDK35/
JDK17/templates. README covers export/render/emulator and physical-device commands.
Key paths: backend/app/modules/{vertical_slice,quests,combat,world}, backend/app/db,
backend/tests/test_folio.py, content/quests, godot_project/scripts/ui/folio_panel.gd,
tools and .github/workflows/foundation.yml. Preserve injected ports and aggregate locks.
