# Changelog

## Unreleased — M0 handoff (2026-09-10)

- Reconcile canonical status with the completed restoration and successful CI.
- Retain signed ARM64 APKs, provenance, verification reports and actual render evidence in CI.
- Fix coplanar coast/floor flicker; fresh desktop render measures 87 draw calls.
- Correct Android landscape orientation. CI run34424981946 passes export, install, touch
  preview/locomotion and background/resume process survival.
- Use ANGLE/SwiftShader after the legacy emulator GLES translator failed shader linking;
  runtime checks now reject engine/render errors explicitly. Strengthen visible-resume
  verification after inspecting the successful run's black transition screenshot.
- Document a reproducible S25 Ultra install/online/thermal test procedure; physical results remain open.
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
