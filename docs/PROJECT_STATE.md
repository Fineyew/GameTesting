# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`; draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → this file → ARCHITECTURE → relevant source before editing.

## Current checkpoint

**Restoration is complete**, saved through `92eb3a3`. Main remains at `bd98746`.
[CI run 34400798944](https://github.com/Fineyew/GameTesting/actions/runs/34400798944)
completed successfully: both backend and Godot jobs. M0 artifact/handoff work remains;
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
- CI: **24 tests passed** with a real PostgreSQL service, migrations 0001→0002,
  save/reload/concurrent action/retry/rollback checks; Godot import and smoke; actual
  Godot account→creation→two-player presence→movement→quest→combat→reward→reconnect.
- Prior desktop render check passed and measured 87 draw calls with default shadows off;
  this is a historical software-renderer observation, not Android performance certification.

## M0 still open

1. Android CI now retains a signed ARM64 APK and passing renders (run34424052563).
   The first emulator run exposed portrait orientation; the fix and rerun are in progress.
2. Fix observed coplanar coastline/floor flicker and rerun visual checks; retain static mesh batching.
3. Reconcile all canonical docs, record exact artifact provenance, test results and device limitations.
4. Save an M0 completion checkpoint before broad M1 production.

An earlier local APK was lost to workspace maintenance. A fresh APK is now retained
in GitHub Actions artifact10131988899; final runtime validation is still pending. Physical phone testing and the updated public host
remain **unverified**. No production deployment occurred.

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
