# Changelog

## 0.2.2 — M1.2 acquisition and folio complete (2026-09-10)

- Code/APK checkpoint 40fcfa7 passes all jobs in run 34434861638: 59 tests / 30 subtests with
  PostgreSQL/migrations, full Godot/API acquisition/folio/reconnect/earned-cast integration,
  89-draw-call render and Android Folio touch/locomotion/visible-resume checks.
- Retain ARM64 artifact 10135899991 (0.2.2/code 4) and runtime evidence 10135900260;
  exact APK SHA-256/source provenance is in PROJECT_STATE. Screenshots inspected.
- Continue M0 at 1044f95 and M1.1 at 4efd3a6/d138214; preserve original content and player IDs.
- Add three small Mara lessons awarding the three existing additional spells, once each.
- Add validated cast objectives, six-slot persistent prepared folio and a touch Folio panel.
- Validate ownership, duplicates, active combat and expected revisions; commit retry receipts
  with state. Combat checks prepared spells while Brace/Gather remain universal.
- Add old-save/forgery/concurrency/acquisition/API/Godot/PostgreSQL regression coverage.
- Bump Android to 0.2.2/code 4; publish ARM64 only after the dependent validation jobs pass.
- Fix resume-check timing for a rotated Android launcher-transition frame; preserve the
  existing world-match threshold and post-resume touch requirement. Physical phone unverified.

- Record the isolated Android startup failure on the documentation rerun; its fresh-runner
  retry passes without changing game code or assertions. Retain full system logcat and a
  final frame for future startup diagnosis; the underlying cause remains unverified.

## 0.2.1 — M1.1 story framework complete (2026-09-10)

- Begin only after M0 checkpoint 1044f95. Preserve the combat engine, world protocol 1,
  persistence adapters, original IDs and Android CI gates.
- Add catalog-driven NPC dialogue with persisted/rotating server cursor IDs, prerequisites,
  ordered objectives, proximity checks and transactional once-only quest rewards.
- Wire Mara's existing graph and one follow-up, An Answer in the Reeds, into Godot.
  Journal/HUD now read quest/objective data. Existing first-quest saves remain valid.
- Add story/API/authoring/old-save/concurrency tests and a real PostgreSQL story gate.
  CI run 34431891977 at 4efd3a6 passes all three jobs: 38 tests with PostgreSQL, Godot
  smoke/full online story, signed ARM64 export, 87-draw-call rendering and Android
  touch/visible-resume checks. APK/runtime evidence retained; physical phone unverified.
- Negotiate story support before login; preserve the existing world protocol and local
  preview content. Version 0.2.1/code 3 APK contains the new story catalog.

## 0.2.0 — M0 engineering handoff complete (2026-09-10)

- Reconcile canonical status and PR #4 with completed restoration and successful CI.
- Complete M0 engineering: 25 backend/PostgreSQL tests, both migrations, Godot client/API
  integration, inspected 87-draw-call renders, retained signed APK and Android runtime gates.
- Retain signed ARM64 APKs, provenance, verification reports and actual render evidence in CI.
- Fix coplanar coast/floor flicker; fresh desktop render measures 87 draw calls.
- Correct Android landscape orientation. CI run 34424981946 passes export, install, touch
  preview/locomotion and background/resume process survival.
- Use ANGLE/SwiftShader after the legacy emulator GLES translator failed shader linking;
  runtime checks now reject engine/render errors explicitly. Run34430377236 at 69457a4
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
