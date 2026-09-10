# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`; draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → this file → ARCHITECTURE → relevant source before editing.

## Current checkpoint

**Restoration is complete**, saved through `92eb3a3`. Main remains at `bd98746`.
[CI run 34400798944](https://github.com/Fineyew/GameTesting/actions/runs/34400798944)
completed successfully: both backend and Godot jobs. Subsequent Android evidence is below;
do not restart restoration or replace the working architecture.

## Implemented and tested

- Modular Godot 4.5.1 client: gateway, creator, third-person capsule movement, orbit/
  spring-arm camera, touch stick, Dawnreef scene, HUD, searchable bag and settings.
- Accounts with Argon2 and legacy PBKDF2 upgrade; character appearance/affinity;
  short access sessions, logout revocation and valid-session renewal.
- Real WebSocket player presence, input authority/collision, snapshots, interpolation,
  reconnection and five preset local phrases. One room/process, 32-player cap unbenchmarked.
- Persisted Tidebeat turns, announced enemy intent, Focus, defense/healing/damage,
  expected-round checks and durable reward receipts. One quest, one enemy, three learned
  starter spells; six spell definitions total, three without acquisition paths.
- JSON development saves plus PostgreSQL adapter and additive migration 0002.
- CI: **25 tests passed** with a real PostgreSQL service, migrations 0001→0002,
  save/reload/concurrent action/retry/rollback checks; Godot import and smoke; actual
  Godot account→creation→two-player presence→movement→quest→combat→reward→reconnect.
- Coastline/floor flicker is fixed; fresh desktop rendering passes at 87 draw calls with
  shadows off. Landscape Android export, installation and touch locomotion pass in CI.

## M0 evidence and final handoff

[CI run 34424981946](https://github.com/Fineyew/GameTesting/actions/runs/34424981946)
for `2101aa4ac769748b4c7d2239e8a85058e0be822e` passed backend, Godot and Android jobs.
The API35 x86_64 emulator installed the QA APK, entered preview with touch, moved through
Dawnreef (22% changed world pixels), and survived background/resume without logged errors.
Visual inspection found the resume screenshot was a black transition frame: the check is
being strengthened to wait for presented terrain and verify touch movement after resume.
Do not confuse process survival with confirmed resumed rendering.

Retained ARM64 artifact **10132315403**: version0.2.0, 27,897,336 bytes, signature verified,
minimum API24/target35. SHA-256:
`28c840ac633374c9c60bd47ba097bfba2de59bd7c74e062fa606a8765542668d`.
Manifest source is `2101aa4`; tested PR merge tree is `daa6cb0`. Runtime evidence artifact
**10132364170**. Both retained until 2026-12-09. Earlier failed-run artifacts are superseded.

Remaining M0 steps: pass the stronger visible-resume check, complete canonical handoff and
save the M0 checkpoint. Physical S25 Ultra/ARM64 testing, thermal/performance/mobile-network
results and the updated public host remain **unverified**. No production deployment occurred.
README contains the physical-device procedure. These remain explicit release gates.

## Placeholder / planned

Procedural art, simple avatar gait/VFX and scripted Mara dialogue. No finished audio,
large authored region, generic branching quests/dialogue, folio editor, equipment/vendor
transactions, gathering/crafting, mounts, housing, pets, dungeon/boss or full moderation.
Account recovery, rotated refresh tokens and physical-device/performance release gates remain.

## Build and test

From repo root: `python -m pip install -r backend/requirements.lock`,
`python -m pytest backend/tests -q`, `python -m tools.build_catalog`.
Set `GODOT_BIN` to Godot 4.5.1; run `python -m tools.check_godot` and
`python -m tools.check_online`. PostgreSQL tests skip without `VT_TEST_DATABASE_URL`;
CI supplies a migrated isolated database. See README for service/client setup.
Important paths: `backend/app/modules/{vertical_slice,combat,world}`, `backend/app/db`,
`godot_project/scripts`, `content`, `tools`, `.github/workflows/foundation.yml`.
