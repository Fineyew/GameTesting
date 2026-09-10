# Changelog

## Unreleased — M0 handoff (2026-09-10)

- Reconcile canonical status with the completed restoration and successful CI.
- Retain signed ARM64 APKs, provenance, verification reports and actual render evidence in CI.
- Fix coplanar coast/floor flicker; fresh desktop render measures87 draw calls.
- Android emulator uncovered portrait orientation; correct the setting and rerun native checks.
- Preserve existing JSON deployments by default; require an explicit PostgreSQL switch/import.
- Close the environment-case bypass of the production PostgreSQL requirement, with regression coverage.

## 0.2.0 — Android foundation restored (2026-09-09)

Saved through `92eb3a3` in draft PR #4. This is a foundation milestone, not the complete authored slice.

- Modular Godot client, touch exploration, camera collision/recentering, original procedural Dawnreef,
  character appearance/affinity, inventory search, settings and explicit offline preview.
- Server-authoritative WebSocket presence, movement validation, snapshots, reconnect and preset chat.
- Deterministic persisted Tidebeat encounters, known-spell/Focus checks and atomic retry-safe rewards.
- Argon2 password storage with legacy upgrade, session version revocation and HTTP auth limiting.
- PostgreSQL aggregate adapter and additive migration 0002; JSON development compatibility retained.
- Six spell definitions; starter quest and enemy remain the playable content scope.
- CI successfully executed PostgreSQL migrations, 24 tests, Godot smoke and actual client/API integration.
- Legacy client scene, original API/source history and foundation database tables preserved.

## 0.1.x — existing repository

Godot account/world shell, starter API/save loop, content validation and
FastAPI/PostgreSQL/Docker architecture. Git history remains authoritative.
