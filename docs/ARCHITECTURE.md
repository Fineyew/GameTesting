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
