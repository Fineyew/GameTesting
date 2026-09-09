# Veilbound Tides — project state

Updated 2026-09-09. Read README, this file, ARCHITECTURE, then relevant source.

## Recovery checkpoint

The September Android foundation session was interrupted before its local feature
branch or artifacts were uploaded. Its transient workspace did not survive.
GitHub main at `bd98746` remains intact. The exact source patches are recorded in
the conversation and are being restored onto `feature/android-foundation`.
Do not replace the original world, APIs, or legacy client from memory.

## Present in the recovered baseline

- Godot account gateway, character hall and local placeholder Dawnreef scene.
- FastAPI registration/login, single character, starter quest/combat/save loop.
- JSON player persistence; PostgreSQL schema and Alembic infrastructure only.
- Content catalog and reference/module-boundary tests.
- Docker, Nginx and deployment runbooks.

## Recorded before interruption; restoration/checks pending

- Modular third-person client and original primitive art; touch stick/orbit camera.
- Authoritative WebSocket presence; preset local phrases.
- Persisted deterministic combat rounds and retry receipts; Argon2 passwords.
- PostgreSQL player-store adapter and second migration.
- Six spell definitions, creation appearance/affinity, searchable satchel.
- 22 backend tests and Godot smoke previously passed; these are historical results.
- A signed ARM64 Android APK previously exported; it is not presently available.

## Next

Restore the recorded files, rerun checks, and save the feature branch remotely.
Then fix overbright lighting and draw calls, test the complete client/server path,
finish PostgreSQL validation and provide a fresh APK. No production deployment
has been performed. Existing game hosting is not verified operational.
