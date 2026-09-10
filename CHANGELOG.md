# Changelog

## 0.2.1 — M1.1 story framework (validation in progress)

- Begin only after M0 checkpoint1044f95. Preserve the combat engine, world protocol1,
  persistence adapters, original IDs and Android CI gates.
- Add catalog-driven NPC dialogue with persisted/rotating server cursor IDs, prerequisites,
  ordered objectives, proximity checks and transactional once-only quest rewards.
- Wire Mara's existing graph and one follow-up, An Answer in the Reeds, into Godot.
  Journal/HUD now read quest/objective data. Existing first-quest saves remain valid.
- Add story/API/authoring/old-save/concurrency tests and a real PostgreSQL story gate.
  Local35 tests, Godot smoke and the extended live client/API story pass; CI reruns pending.

## 0.2.0 — M0 engineering handoff complete (2026-09-10)

- Reconcile canonical status and PR #4 with completed restoration and successful CI.
- Complete M0 engineering: 25 backend/PostgreSQL tests, both migrations, Godot client/API
  integration, inspected 87-draw-call renders, retained signed APK and Android runtime gates.
- Retain signed ARM64 APKs, provenance, verification reports and actual render evidence in CI.
- Fix coplanar coast/floor flicker; fresh desktop render measures 87 draw calls.
- Correct Android landscape orientation. CI run34424981946 passes export, install, touch
  preview/locomotion and background/resume process survival.
- Use ANGLE/SwiftShader after the legacy emulator GLES translator failed shader linking;
  runtime checks now reject engine/render errors explicitly. Run34430377236 at69457a4
  also proves visible world recovery and repeat touch locomotion after resume.
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
