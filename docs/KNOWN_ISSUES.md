# Known issues and limitations

Updated 2026-09-10. See PROJECT_STATE for current CI/artifact status.

## Release gates

- Updated public server not deployed or verified. Online play needs a protocol 1 server.
- Physical Android install/touch/safe-area, 20-minute thermal/memory/battery, packet-loss,
  cellular/Wi-Fi switching and background/resume certification remain outstanding.
  CI emulator and desktop rendering cannot substitute for these measurements. The emulator
  gate exercises offline exploration, Folio and Bag/vendor touch; online progression is tested with Godot/API integration.
- Recovery/email verification/opaque rotated refresh tokens/remembered secure credentials
  and admin account workflows are unfinished. Access-token renewal needs a valid token.
- Existing JSON accounts require backup and explicit preserved-ID import before changing
  a live service to PostgreSQL. Migration 0002 does not import JSON. Restore drills remain.
- Only preset chat is exposed. Free text, blocking/reporting and moderation are unfinished;
  user-name moderation also needs a release design.
- Debug keys are ephemeral, so later test APKs can need uninstall/reinstall. Release signing,
  AAB/store rollout and a permanent updater identity are not configured.

## Gameplay/art

- One enemy and five quests, including three short lessons; six obtainable spells and an
  editable six-slot folio. Affinity-specific progression and cooperative combat remain planned.
- Catalog-driven Mara dialogue and one investigation now exist. Collect-item/repeatable
  quests, broader objective types and visual authoring tools remain planned. M1.1 integration
  and Android gates pass at 4efd3a6; additional NPC visual/interaction bindings need scene work.
- One vest vendor/equipment loop is implemented; full M1.3 gates are pending. Item use, selling,
  trading, wearable vest mesh, additional gear slots, gathering/crafting, mounts,
  housing, pets, dungeon/boss and most social features are not implemented.
- Procedural models, gait, primitive spell impacts and flat region remain placeholders.
  No finished audio framework, soundtrack, skeletal animation or production asset kit.
- Capsule/gravity/floor snap exist, but server movement is planar. Stairs, slopes and vertical
  authority are not tested. Full UI scaling, safe areas, left-handed controls and menu controller
  support remain accessibility work.

## Engineering

- M0 Android emulator checks pass at 69457a4, including visible resume and repeat touch
  locomotion. The earlier black transition screenshot is resolved by waiting for presented
  frames; this was a test timing gap. Physical-device gates above remain open.

- One process/room. No multi-worker routing, instanced party ownership, interest management
  or load test. Slow sends may stretch fixed ticks; cellular TCP behavior needs profiling.
- Receipt retention is 128 responses per character. Expected rounds/encounter IDs protect old
  action replay, but large JSONB payloads need normalization before substantial growth.
- JSON store is single-process development only. Disk-full/backup recovery needs operational tests.
- Legacy one-shot combat remains a capped compatibility path; retire/gate it before a public economy.
- Content checksums/bundled catalog exist; downloadable packs, signature verification, repair,
  resumable downloads and patch UI are planned. Several initial asset references are unbuilt.
- Structured telemetry/correlation/audit trails and full operational monitoring are incomplete.
- Docker runtime/public deployment are unverified here; CI proves the application and database
  behavior in its isolated test environment, not the production topology.

- M1.2 full gates pass at d0c6048/run 34437004626. The d138214 docs-only rerun failed on a
  portrait launcher-transition screenshot; waiting for landscape presentation resolved it
  without relaxing the view-match threshold. This is not physical-device certification.

- Documentation checkpoint 8105f4a's first Android attempt timed out before gateway startup,
  with an emulator graphics-buffer error and Godot `_start_success` cleanup error. The
  identical game code passed the complete native gate at 40fcfa7. The isolated Android rerun
  passed all native gates (run 34435465708, attempt 2), without changing game code or tests.
  The underlying startup cause remains unverified. Full system logcat and a final frame
  are now retained on test exit to help diagnose another occurrence. Do not weaken startup,
  error-log, visible-frame or touch gates to hide a failure. Failed runs publish no ARM64 APK.

- The 9b66c0a native run caught a stale gateway screenshot used as the exploration baseline.
  Folio close worked; the baseline capture was early. The check now requires the visible
  player plaque/thumb control in exploration frames as well as landscape/terrain. Existing
  comparison thresholds are unchanged; the captured failing frame is rejected by the new
  predicate and captured exploration/resume frames are accepted. Full CI passes at d0c6048
  (run 34437004626); the new exploration baseline and native Folio/resume frames were inspected.
