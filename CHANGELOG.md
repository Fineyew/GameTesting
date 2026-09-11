# Changelog

## 0.2.5 — M1.5 bandage loop candidate (2026-09-11)

- Continue from a5d06db after its full CI passed; owner requested continued engineering.
- Use one owned Sunthread Bandage outside combat: up to12 Vigor, cap30, no waste at full health.
- Reuse aggregate locks, commerce revision and durable receipts for atomic consumption/healing.
- Enable the existing five-chit listing (shop version3); add Bag Vigor, effect and use feedback.
- Add item_use_protocol1 and strict item-use API/content validation; no DDL or new save fields.
- Add JSON/API/concurrency/rollback/content and PostgreSQL use/purchase regressions, real
  Godot/API purchase/use/reconnect and scroll-visible GUI input coverage.
- Local97 backend tests/30 subtests pass;9 PostgreSQL tests await CI. Godot/API passes.
  Candidate f761714/run34547305384 passes backend106/30 including9 PostgreSQL tests,
  Godot/API and render. Native resume swipe was sent during an Android window transition
  and failed; retain artifact10179708379, publish no APK. Wait for stable focused/idle
  window state before the single swipe; all movement thresholds remain unchanged.
- Route item-use server errors into the existing recovery UI; add an actual Godot/API
  stale-use/reload regression that verifies unchanged Vigor, inventory and revision.
  Corrected full CI and ARM640.2.5/code7 pending. Physical acceptance remains unverified.

## 0.2.4 — M1.4 visual benchmark candidate (in progress, 2026-09-10)

- Continue the revised roadmap from edec97b; preserve completed M0–M1.3 checkpoints.
- Add original editable Blender sources and exported well/cart/house/foliage kit.
- Replace the sample Wayfarer/Mara placeholders with tinted 13-bone rigs and idle/walk/cast.
- Present confirmed Glimmer casts with framing, anticipation, trail, impact and cleanup;
  add a saved short-effects/no-camera-cut setting. No server rules or protocols changed.
- Add ground/contact shading and compatible HUD borders; preserve collision geometry.
- Add source/GLB budgets, rig/VFX smoke and retained render/triangle/texture evidence.
- Candidate b5b90a5/run34478939955 passes backend90/30, Godot/API and desktop74-call render.
  Native resume comparison failed at19.35%; artifact10152976777 retained, no ARM64 published.
  Preserve imported kit transforms, clear pause movement and require a settled baseline
  while retaining all existing native movement/resume thresholds. Add matching route movies
  and keep render diagnostics on failures. d9293fa/run34480660769 passes all full gates,
  retains ARM64 0.2.4/code6 and both matched route recordings. Visual review leads to a
  final bounded canopy/cast-camera, paving and shop-side cleanup.
- Code checkpoint 365993ce7e79fc29025ee23d1c77cbf449ad2bfc passes all gates in
  run34483308643: 90 tests / 30 subtests with 8 PostgreSQL tests and both migrations,
  strict Godot/art/two-player API checks, inspected 71-call/83,630-primitive render,
  matching 30.83-second movies and native touch/visible-resume/repeat-movement checks.
- Retain verified ARM64 0.2.4/code6, 29,144,004 bytes, artifact10154911714;
  native10154913361 / render10154915083. SHA256
  d5ba342559fc0a19e0bcdc6133128415dce30467ff796b2a392d7a66ae0f65ab.
- Reconcile canonical docs and PR handoff with the verified code/artifact and corrected
  forward ordering. M1.4 owner art acceptance and physical-phone Device E remain open;
  M1.5 is unstarted. No merge, public deployment or completed-milestone claim.

## 0.2.3 — M1.3 vendor/equipment complete (2026-09-10)

- Code/APK checkpoint de9d7a3 passes all gates on the first attempt in run34440512749:
  90 tests/30 subtests, eight PostgreSQL tests/migrations, full Godot/API progression,
  inspected 89-draw-call vendor/equipment renders and native touch/visible-resume QA.
- Retain ARM64 0.2.3/code5 artifact10137878626 and runtime evidence10137878970;
  27,914,052 bytes, SHA256 cd4c196dc7d679f6c64aa978f8c16fb08a7e2a8c1ec03c5ba5d9e34bdec568fb.
- Continue M1.2 at d0c6048/56370e6; its final handoff run34437584787 passed all jobs.
- Activate existing Dawnreef Supply Cart and Lanternkeeper Vest for 12 earned chits.
- Add server-owned atomic purchases, catalog prices, inventory/level/slot checks and
  persistent commerce revisions with existing retry receipts and aggregate locks.
- Equip/unequip the chest item; derive Guard1 from catalog/ownership at encounter start.
  Preserve appearance, six-spell folio, Tidebeat rules without gear, story IDs and saves.
- Add touch Bag/vendor panels, useful Guard comparison, state/feedback/search/retry UI.
- Leave bandage purchase unavailable until item use exists; no broad content expansion.
- Add JSON/PostgreSQL/API/old-save/concurrency/rollback and Godot interaction regressions.
- Bump to Android0.2.3/code5; retain vendor/equipment renders and native Bag→vendor touch.
  PostgreSQL/backend90 tests and Godot/API pass in run34439273721. Initial native validation
  failed on a Pixel Launcher ANR overlay, retained in artifact10137449675; identical rerun
  reached native navigation and caught an input-time panel-detachment error. Hide/queue
  retiring controls so Godot can finish input dispatch; strengthen all Godot error gates
  and dispatch GUI input in smoke. Full corrected validation passes atde9d7a3; both failed
  attempts published no ARM64 artifact. Record failure evidence without weakening tests.
  Physical phone remains unverified.

## 0.2.2 — M1.2 acquisition and folio complete (2026-09-10)

- Code/APK checkpoint d0c6048 passes all jobs in run 34437004626: 59 tests / 30 subtests with
  PostgreSQL/migrations, full Godot/API acquisition/folio/reconnect/earned-cast integration,
  89-draw-call render and Android Folio touch/locomotion/visible-resume checks.
- Retain ARM64 artifact 10136657783 (0.2.2/code 4) and runtime evidence 10136658341;
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

- Correct the stale-gateway exploration baseline exposed by native Folio validation: wait
  for the actual player HUD before comparing frames. Keep all comparison thresholds.
- Correct the startup footer to 0.2.2; gameplay rules/content and save formats are unchanged.

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
