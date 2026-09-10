# Known issues and limitations

Updated 2026-09-10. See PROJECT_STATE for current CI/artifact status.

## Release gates

- Updated public server not deployed or verified. Online play needs a protocol 1 server.
- Physical Android install/touch/safe-area, 20-minute thermal/memory/battery, packet-loss,
  cellular/Wi-Fi switching and background/resume certification remain outstanding.
  CI emulator and desktop rendering cannot substitute for these measurements. The emulator
  gate exercises offline exploration; the full online story is tested with Godot/API integration.
- Recovery/email verification/opaque rotated refresh tokens/remembered secure credentials
  and admin account workflows are unfinished. Access-token renewal needs a valid token.
- Existing JSON accounts require backup and explicit preserved-ID import before changing
  a live service to PostgreSQL. Migration 0002 does not import JSON. Restore drills remain.
- Only preset chat is exposed. Free text, blocking/reporting and moderation are unfinished;
  user-name moderation also needs a release design.
- Debug keys are ephemeral, so later test APKs can need uninstall/reinstall. Release signing,
  AAB/store rollout and a permanent updater identity are not configured.

## Gameplay/art

- One enemy and two quests; three learned spells. Three additional engine definitions have
  no acquisition path. No editable folio, affinity-specific progression or cooperative combat.
- Catalog-driven Mara dialogue and one investigation now exist. Collect-item/repeatable
  quests, broader objective types and visual authoring tools remain planned. M1.1 integration
  and Android gates pass at 4efd3a6; additional NPC visual/interaction bindings need scene work.
- Inventory search/quantities exist; equip/use/compare, vendors, gathering/crafting, mounts,
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
