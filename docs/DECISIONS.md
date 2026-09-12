# Decisions

| ID | Decision | Reason / boundary |
|---|---|---|
| D001 | Continue Veilbound Tides/Auralis/Dawnreef | Repository and original content identity are authoritative. |
| D002 | Pin Godot 4.5.1 Compatibility renderer | Reproducible mobile export; reversible after profiling; not a latest-version claim. |
| D003 | Retain FastAPI/PostgreSQL/Docker/Nginx | Inexpensive self-hostable modular monolith; no new paid managed infrastructure. |
| D004 | WebSocket presence alongside HTTP commands | Owner requires real visible multiplayer, superseding older deferral advice. |
| D005 | One room owner, 20 Hz input authority/10 Hz snapshots | Simple measurable foundation;32 cap is not load certification. No multi-worker deployment yet. |
| D006 | Tidebeat with visible intents and Focus | Tactical preparation without random hand draws; six-slot folio implemented in M1.2; co-op later. |
| D007 | Aggregate transactions plus durable response receipts | Atomic rewards and protection from retries/concurrent actions. |
| D008 | Additive PostgreSQL runtime row, JSON local compatibility | Preserve identity tables and old development saves; explicit migration/import before switching live stores. |
| D009 | Argon2 with legacy login upgrade; versioned short sessions | Preserve accounts while improving credentials; full recovery/refresh-token lifecycle remains unfinished. |
| D010 | Preset chat first | Real social presence while free-text moderation/block/report safeguards are built. |
| D011 | Explicit offline exploration preview | Never fabricate secure offline multiplayer progress. |
| D012 | Preserve legacy client; modular new main scene | Keep history and working source while separating camera/movement/UI/network responsibilities. |
| D013 | Remote checkpoints and canonical state before handoff | Workspace maintenance can remove local files; conversation memory is not durable source. |
| D014 | Retain Android CI artifacts and separate emulator QA build | Recoverable builds and runtime evidence; x86 emulator success cannot certify ARM64 phone performance. |
| D015 | Server-owned dialogue cursor and catalog quest rules after M0 checkpoint 1044f95 | One optional cursor in the existing aggregate, immutable catalog, transactional progress/rewards; no new database or world server. |
| D016 | Six-slot server-owned folio, explicit preparation, revision-checked updates | Preserve known spells/old saves, block combat edits and stale retries; universal Brace/Gather need no slot. |
| D017 | Three small quest-based spell lessons, including server-observed casts | Meaningful sources for existing spells without changing completed rewards or generating more families/regions. |
| D018 | One existing chest item with catalog Guard1, separate appearance | A meaningful earned purchase without stat bloat, new gear families or cosmetic penalties; no wearable mesh/transmog claim. |
| D019 | Commerce revision + existing aggregate lock/receipts; catalog shop version | Atomic spend/grant, cross-connection overspend protection, safe retries after receipt eviction and stale-price rejection; reuse both adapters. |
| D020 | Preserve unavailable bandage listing until item use is implemented | Avoid selling a nonfunctional consumable while retaining existing IDs and reward inventory; originally candidate M1.4; roadmap edec97b schedules it as M1.5. |
| D021 | Hide retiring modal controls, then queue deletion at frame end | Native touch retained the emitting control during dispatch; synchronous detachment caused can_process errors. Preserve actual adb touch and strict engine-error gates. |
| D022 | Prove a small Dawnreef art benchmark before wider production | Roadmap edec97b moves bandages to M1.5; art acceptance and actual phone measurements gate copying the kit. No server redesign. |
| D023 | Editable Blender sources outside Godot, checked-in self-contained GLBs | Original reusable assets, deterministic recipes, named rigs/materials and import budgets without Blender on game CI or phones. |
| D024 | Confirm combat first, then bounded presentation with a short-effects option | Keep server authority/receipts and make a significant spell visible without forcing repeat camera cuts. |
| D025 | Separate camera-only foliage from catalog movement collision | Improve orbit/cast visibility without client-only movement blockers, protocol changes or server shortcuts; test both actor sightlines. |

- D026 (2026-09-11): Following the owner's repeated continuation instruction after the
  device handoff, advance narrow engineering checkpoints while retaining unverified physical
  acceptance. Do not label M1.4/M1.5 fully accepted or release-ready from automated tests.
- D027: Reuse commerce transactions/revisions/receipts for single-item out-of-combat healing;
  preserve old saves, separate rules from persistence, and consume nothing at full Vigor.

- D028: Gate emulator gestures on the actual API35 focused/visible surface and rotation
  state, retaining diagnostics and a bounded stabilization wait. Legacy transition fields
  are absent; test the recorded dump shape and fail closed on missing/hidden surfaces.
  Keep one gesture and the existing visual thresholds; do not claim real-phone certification.

- D029: Extend the existing CLI/catalog/native-editor workflow for M1.6. Keep authoring
  examples outside live content and preview them through an isolated real client/API/store.
  Asset metadata validates bindings/evidence without claiming it can implement handlers
  or certify visual/device quality. No CMS, runtime protocol or schema redesign.

- D030 (2026-09-11): Begin M1.7 with strict validation of the currently executable planar
  geometry before introducing height data. Pin capsule agreement, reject unsupported
  elevation fields and preserve production catalog bytes. ARCHITECTURE records the next
  shared triangular-cell surface, protocol2 handshake and derived-height save plan; these
  runtime changes remain planned until parity/integration/Android gates pass.

### M1.7 surface parity before activation (2026-09-12)

Checkpoint surface queries/triangles independently from movement activation. Physical
raycasts complement numeric parity because two languages can agree on wrongly wound
collision faces. Integral JSON numbers are accepted in both runtimes because Godot's
JSON parser represents numbers as floats; booleans and fractional millimetres are rejected.
Generated Fal assets remain source candidates outside the runtime export until art,
license, import and Android budget acceptance; paid generation is not production approval.
