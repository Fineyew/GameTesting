# Veilbound Tides — current architecture

Retain the existing Godot 4 client, modular FastAPI backend, PostgreSQL target,
Docker Compose and Nginx. Historical detail remains under docs/architecture/;
this document and explicit current owner instructions govern subsequent changes.

## September direction

The owner explicitly requires real visible multiplayer presence, superseding the
older recommendation to defer WebSocket infrastructure. The implemented versioned, low-rate
WebSocket world channel retains HTTP for accounts/content/durable combat
commands. One process owns a capped room initially; multiple independent workers
must not be enabled until room ownership and session routing are externalized.

The inherited JSON save is a development/compatibility adapter. The PostgreSQL
adapter reuses account/character identity tables and adds one locked runtime-state
row per character containing the current slice aggregate and retry receipts.
Normalize into module tables through migrations when actual feature boundaries
require it; do not fabricate production scale or database verification.

The new Godot client separates bootstrap, play session, UI, world assembly,
character motion, camera, avatars and network transport. Preserve the legacy
client scene and API while validating the new main scene.

## Authority

Clients submit movement input, spell choices and command identifiers. Servers
choose/validate ownership, position, damage, progress and rewards. Round numbers,
encounter identifiers and durable receipts prevent retry rewards. Offline preview
has no persistent progress. Real-time transport and authoritative movement are
independent of the HTTP character/economy state interface.

## Continuity

The September foundation restoration is complete and checkpointed through `92eb3a3`.
CI run 34400798944 executed both migrations, 24 tests, Godot smoke and client/API integration.
Android export retention and device verification remain separate M0 gates.
PROJECT_STATE records actual restoration/verification, not design aspirations.
Push stable feature-branch checkpoints during long sessions and update state
before handoff. No secrets or build products belong in source control.

## Implemented interfaces and runtime constraints

The composition root (`backend/app/main.py`) injects the immutable content catalog,
player store, `CombatEngine`, `EncounterService` and `WorldHub`. Existing boundary tests
forbid cross-module internal imports and gameplay imports of database infrastructure.
The PostgreSQL adapter implements the same aggregate-store contract as local JSON saves.

The active Godot main scene is `scenes/app/bootstrap.tscn`. `PlaySession` orchestrates
HTTP/WS, HUD and encounters; character motion, avatar, orbit rig, touch stick, theme and
world assembly remain separate. Preserve `scenes/vertical_slice_client.tscn` as legacy.
Source catalog JSON is validated and bundled by `tools/build_catalog.py`. The client
checks server world_protocol=1 and matching geometry before entry.

WebSocket `/api/v1/world/socket` authenticates in its first message (type=auth,
protocol=1, token, character_id); tokens never belong in query strings. One process owns
Dawnreef, at most 32 players: 20 Hz integration, 10 Hz snapshots. Move messages carry bounded
monotonic seq and finite axis:[x,z]; the server integrates speed/acceleration and checks
expanded rectangular blockers/bounds. Remote avatars interpolate; local motion reconciles.
Stale input stops after 0.4s, idle/expired sessions disconnect, positions checkpoint every 5s
and on departure. Reconnect uses backoff/jitter; replacement closes the prior socket.
Only five phrase IDs are allowed for local chat, with a 2s cooldown. No free text exists.

HTTP `POST /world/characters/{id}/encounters` requires proximity and an Idempotency-Key.
Actions submit encounter_id, action and expected_round to `/encounters/actions` with
the same key on retries. The server checks ownership, spell knowledge and Focus; chooses
damage, outcomes and rewards. A transaction saves state and response receipt together.
Matching retries replay the saved response; changed payloads with reused keys fail.
Round and encounter IDs still reject old action replay after the 128-receipt retention cap.
An active encounter is private persisted state, not a separate live 3D server scene.
Co-op/dungeon/housing instance ownership and room routing remain future boundaries.

Migration 0002 adds `accounts.auth_version` and `character_runtime_states` (character_id
PK/FK, schema_version, JSONB payload), retaining all foundation tables. Account/character
identity data remains in original tables. PostgreSQL transaction-scoped advisory locks
serialize aggregate commands; rewards and receipts commit together. JSON uses a process
lock, rollback copies and atomic file replacement, and is development-only. Do not run
multiple writer processes or add competing writers to normalized/aggregate state.

New passwords use Argon2; successful PBKDF2 logins upgrade hashes. Access JWTs expire in
15 minutes by default and carry session_version. Logout revokes the version and closes
world sockets. `/auth/refresh` renews a still-valid access session; opaque refresh tokens,
recovery, email verification and remembered secure credentials are not yet implemented.

Nginx terminates HTTPS and forwards WebSocket upgrade headers. Keep one application
process; multiple Uvicorn workers would create independent inconsistent rooms. Migrations
run explicitly before enabling PostgreSQL. Back up/import existing JSON saves preserving
IDs, balances and progress before switching a live service. The runtime migration alone
does not import players, and no production deployment has been performed here.

## Android and evidence pipeline

The pinned client uses GDScript, Godot 4.5.1 Compatibility, JDK17 and SDK/build-tools 35.
`tools/export_android.py` creates a signed ARM64 debug APK and an optional separate
x86_64 emulator QA APK, restores the checked-in preset after export, verifies signatures
and manifest fields, and records SHA-256/source commit. Keys are local ephemeral debug
identities, never release credentials. The engine export declares minimum API24/target35.
Windows has a preset but no validated export; iOS remains planned.

CI retains APK/provenance and desktop frames, then installs the QA APK on an API35
emulator and uses actual adb touch input to enter preview/move, background and resume.
Logs/screenshots record the result. These are runtime/function checks, not physical ARM64
performance certification. Source checkpoints persist in Git; downloadable artifacts
must also be retained. Current startup has no pack download/repair/resume updater yet.
