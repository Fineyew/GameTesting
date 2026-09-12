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
M0 engineering gates now pass through69457a4: retained signed ARM64 export and emulator
installation/touch/visible resume. Physical ARM64 performance remains a separate release gate.
PROJECT_STATE records actual restoration/verification, not design aspirations.
Push stable feature-branch checkpoints during long sessions and update state
before handoff. No secrets or build products belong in source control.

## Implemented interfaces and runtime constraints

The composition root (`backend/app/main.py`) injects the immutable content catalog,
player store, `CombatEngine`, `EncounterService`, `QuestRules`, `StoryService`, `InventoryRules`, `CommerceService` and `WorldHub`. Existing boundary tests
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
the same key on retries. The server checks ownership, prepared folio membership, spell knowledge and Focus; chooses
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
Logs/screenshots record the result. Before the post-resume swipe, the API35 harness
requires three seconds of a focused, visible, shown landscape app surface with no screen
rotation animation. It retains the OS window dump and fails closed on missing fields.
Seven parser/readiness regressions run in the Android job. No extra gesture is injected;
the original movement and resume-difference gates remain unchanged. These are runtime/
function checks, not physical ARM64 performance certification. Source checkpoints persist in Git; downloadable artifacts
must also be retained. Current startup has no pack download/repair/resume updater yet.

CI uses the supported `swangle` emulator graphics mode (ANGLE over SwiftShader).
The legacy `swiftshader_indirect` path produced GLES shader-link failures and blank
frames, caught by screenshot comparisons. See Android's
[graphics acceleration modes](https://developer.android.com/studio/run/emulator-acceleration).
This changes the test driver, not the game's Compatibility renderer. The runtime gate
rejects engine/render errors and requires visible movement from real touch input.

## M1.1 story rules and persistence

The composition root injects `QuestRules` alongside the existing combat engine. It reads
the same catalog through ContentReader, owns condition/objective/dialogue interpretation,
and imports no other gameplay module or database implementation. `StoryService` remains
in vertical_slice as aggregate transaction orchestration. The original starter-only
accept/fight APIs and standalone legacy service behavior are preserved. New quests are
accepted through validated NPC offers; combat emits server-observed defeat events into
the injected quest rules while retaining the existing encounter receipts and rewards.

POST `/world/characters/{id}/npcs/{npc}/dialogue` opens a server-selected branch; `/choose`
accepts only conversation_id and option_key. One cursor per character stores NPC, graph
version, node and a rotating UUID. Stale/reordered/forged choices fail; clients cannot send
node jumps or reward amounts. POST `/interactions/{key}/inspect` accepts no completion
claim: the server checks ownership/live world proximity and the catalog's discovery.
Combat blocks story interactions. Quest events are ordered when declared; discoveries
and talk objectives have quantity 1. Nonrepeatable completion/rewards_claimed flags commit
with XP/items/currency under the existing aggregate lock, so retries cannot reward twice.
After an uncertain choice response, reopen the conversation; saved progress is retained.

`CharacterRecord.dialogue_state` is an optional dictionary, defaulting empty for old JSON
and PostgreSQL JSONB saves. It is excluded from public character responses; dialogue APIs
return a sanitized view. This is additive within runtime schema 1 and needs no DDL migration.
An older server binary cannot read newly added aggregate fields: backup before rollback,
and migrate/drop only this cursor field deliberately if downgrading to M0. Never reset
player IDs, inventory, quest progress or rewards. Protocol1 movement/geometry is unchanged.
`/server-info` adds story_protocol=1; the 0.2.1 client checks it before authentication,
so an older backend fails with a clear update message instead of partial story support.
Older clients can still use the unchanged world protocol and starter compatibility API.

The first authored follow-up uses existing landmarks and rewards 40 XP/5 shell chits once.
It does not open the cistern dungeon or add harvesting, folios or additional spells.

M1.1 verification is complete at 4efd3a6/run 34431891977:38 backend tests with PostgreSQL,
actual Godot online story traversal and retained Android export/touch/visible-resume
evidence. APK/runtime artifact IDs and source hashes live in PROJECT_STATE.

## M1.2 folio and acquisition

`FolioService` is injected at the existing composition root; it shares the aggregate
transaction/lock and receipt map with combat. POST `/world/characters/{id}/folio` takes
only spells (1–6 unique catalog keys) and expected_revision (nonnegative integer), plus
Idempotency-Key. Ownership, spell knowledge and inactive combat are validated server-side.
Successful updates increment folio_revision and save state/receipt atomically. Matching
retries replay the response; changed payloads fail. Revision checks reject stale writes
even after the 128-receipt cap. Another session must reload before editing stale state.
The client reloads current state after a successful receipt, since a replay may predate
another update. A failed response retains the exact request/key for retry or explicit reload.

CharacterRecord adds optional `folio` and `folio_revision=0` within schema 1. Missing/null
folio becomes the first six distinct already-owned spells; existing IDs, quests, inventory,
active encounters and receipts remain. Both JSON and PostgreSQL deserialize through the
same dataclass; no DDL migration is needed. Back up before downgrade: older binaries need
these new fields removed deliberately as well as the M1.1 cursor, without resetting players.
`folio_capacity=6` is a public constant, not a writable character field.

Encounter start snapshots only the prepared spell rules. Preparation is locked while an
encounter is active; every non-universal action also checks current ownership/preparation.
Existing M1.1 active encounters resume with their starter folio. Brace/Gather and Tidebeat
Focus/intents/effects are unchanged; the legacy fight endpoint now enforces preparation.

QuestRules adds learn_spell rewards and cast_spell observations (optional enemy/intent
threshold), passed by EncounterService after legal resolution. The same transaction commits
cast credit, combat results and receipts; the existing once-only quest flags protect spell
acquisition. Learned spells are not automatically prepared. No new client authority or WS
messages: world1/story1 remain, and server-info adds folio_protocol=1 checked before login.

The client adds FolioPanel inside the existing HUD modal. Selection is a local draft until
saved by the server; cards derive cost/effects/source hints from the catalog. Online Godot
integration learns all three spells, changes folio through UI signals, reconnects, verifies
rejection of an unprepared spell, and casts earned Seam Lance. Native QA opens/closes the
folio by touch in preview; this is separate from authoritative online progression coverage.

Android CI now waits for backend/Godot gates and publishes ARM64 artifacts only after
render and emulator validation succeed. The docs-only d138214 rerun exposed a portrait
launcher-transition screenshot during resume: the gate now waits for landscape presentation
before applying the unchanged view-match threshold and repeat-touch check. It does not
rotate evidence or certify physical-device behavior.

M1.2 engineering verification is complete at d0c6048/run 34437004626: 59 tests with
PostgreSQL, full Godot/API flow and signed ARM64/native Folio-touch/resume evidence.
PROJECT_STATE records artifact IDs, exact hashes and the unverified physical-device gates.

The native test always retains filtered game logs, full system logcat and a final frame,
including failures before the gateway marker. This follows an isolated startup failure on
8105f4a (engine cleanup/emulator graphics-buffer errors); its Android-only rerun passed
unchanged. The cause remains open in KNOWN_ISSUES, not hidden by relaxed assertions.

Exploration captures also require the player plaque and resting thumb control. The green
terrain alone cannot distinguish the gateway background from a newly entered world;
ready logging can precede presentation on the emulator. This prevents using a gateway
frame as a movement/Folio-close baseline while retaining the original comparison limits.

## M1.3 vendor/equipment boundaries

The composition root injects catalog-only `InventoryRules` into `CommerceService` and
`EncounterService`. Rules stay in the inventory module; aggregate transactions stay in
vertical_slice. No cross-module internal imports or database dependencies were added to
gameplay. Both existing persistence adapters and migrations remain unchanged.

GET `/world/characters/{id}/shops/{shop}` returns current prices, availability, owned/equipped
state and Guard comparison. New buys require live proximity to the shop's catalog NPC,
the correct zone and inactive combat. GET `/world/characters/{id}/equipment` returns the
bag and derived equipment stats. Both views check ownership under the aggregate lock.

POST `/shops/{shop}/buy` accepts only listing_key, quantity, shop_version and expected_revision.
POST `/equipment` accepts only slot, item_key (null to unequip) and expected_revision. Both
require Idempotency-Key. Strict integer bounds and forbidden extra fields reject arbitrary
price, currency, inventory and stat claims. The immutable server catalog chooses grant,
price, stack cap, level requirement and slot/stat legality. shop_version forces a price
reload after a catalog update, preventing a stale displayed quote from being charged.

A shared optional `commerce_revision=0` serializes successful buy/equip/unequip commands.
Within the same existing character transaction: authenticate ownership, replay a matching
receipt or reject a conflicting key, check revision/combat/proximity/rules, deduct/grant
or equip, increment revision, save state and response together. No network calls occur
under the database lock. PostgreSQL advisory transaction locks serialize independent
connections; JSON retains its process lock, rollback copy and atomic file replacement.
Matching retries can replay after leaving the shop; new purchases still require proximity.
Revision checks reject stale commands after the shared 128-response receipt cap. Currency
and inventory are re-read under lock even when another quest/combat action changed them.

The existing equipment map persists slot→owned item key. No client or saved stat fields
are trusted: Guard derives from validated owned/level-legal catalog equipment and is
snapshotted at encounter creation. Old active encounters without equipment_guard resolve
with zero gear bonus. Unequipping preserves the item. Appearance stays separate and is
never changed by equipment; no mesh/transmog system is claimed. Schema1 optional fields
preserve old saves without DDL. An M1.2 downgrade requires deliberate removal of
commerce_revision and encounter equipment_guard after backup; it cannot support gear
benefits. Never reset player IDs, quest/folio state, currencies or inventory.

`commerce_protocol=1` is an additive server-info capability checked by client0.2.3 before
login. World1/story1/folio1 are unchanged; public online play needs this branch's backend.
CommercePanel lives inside the existing HUD modal and Bag/Mara navigation. It uses server
views, search, large touch buttons, comparison, saved feedback and exact-request retry or
reload. After a confirmed command it fetches current state, since a receipt may be old.
Offline catalog views are explicitly nonpersistent previews with disabled buy/equip.

The Godot/API gate earns currency, buys, equips, unequips, reconnects and proves Guard
in actual combat while retaining the entire M1.1/M1.2 flow. Native Android additionally
opens Bag→vendor by adb touch; it covers preview/navigation, not online transaction logic.
Render evidence includes vendor and equipment panels. ARM64 publication remains after
all backend/Godot/render/emulator gates; physical-device validation remains separate.

Modal replacement hides retiring controls and queues their deletion; it does not detach
controls synchronously inside a button callback. Android input dispatch can still refer
to the pressed control after the callback returns. This follows Godot's
[queue_free lifecycle](https://docs.godotengine.org/en/4.5/classes/class_node.html#class-node-method-queue-free).
The native Bag→vendor gate caught the previous can_process error; smoke now dispatches
GUI mouse input and all Godot gates reject engine errors as well as script failures.

M1.3 complete code/APK checkpoint de9d7a3 passes all gates in run34440512749: 90 tests /
30 subtests with eight PostgreSQL tests/migrations, full Godot/API progression, 89 draw
calls and native Bag/vendor/Folio/movement/visible-resume checks. PROJECT_STATE records
exact APK provenance and open physical-device/public-deployment gates. The initial
Pixel Launcher overlay and subsequent real panel error remain documented with retained
failure evidence; the corrected run passes without relaxing any native assertion.

## M1.4 visual benchmark boundary (candidate)

`DawnreefArt` assembles eight reusable imported mesh pieces inside the existing zone's
flat footprint. The first house keeps exactly the catalog collision rectangle; its visual
room/cart occupy that rectangle. World protocol1 and the geometry digest do not change.
Other houses, distant scenery, the lurker and cistern remain explicit placeholders.

Editable `.blend` files and deterministic source recipes live outside the Godot project
in `art_sources`; checked-in GLB/import settings are runtime inputs. Ordinary CI/export
does not require Blender. The small manifest records status, provenance and mesh budgets;
`tools.check_art` verifies self-contained glTF, materials, vertex colors, rigs and clips.
Godot generates mesh LODs on import. Static batches retain every material surface and
shadow policy, leaving collision children active. Contact shadows are small transparent
planes; optional real shadows retain the existing user preference. Ground washes use
a two-scale shader with no texture assets. Render gates retain actual frames and enforce
150 default draw calls, 150k primitives and 128 MiB textures; these are not phone timings.

`WayfarerAvatar` preserves build/appearance/walking for local and remote players while
loading the sample rig. Tint materials are shared by the finite appearance palette,
which also keeps their lifetime valid during engine teardown. Animation speed follows
movement; the imported three-clip sample is not the full M1.8 locomotion library.

`GlimmerPresentation` is visual only. PlaySession waits for a confirmed action receipt,
updates authoritative character state, freezes movement while busy and then plays the
bounded visual before returning to the combat panel. The effect cannot calculate damage
or grant progress. Pending commands retain existing retry rules. A saved local setting
shortens effects and avoids the temporary camera cut. No schema/HTTP/WS changes.

M1.4 validation also records the same preview route against preserved M1.3 and the current
source, at identical camera/control/quality settings. Movie Maker recordings demonstrate
art/motion only; fixed capture FPS cannot establish runtime frame pacing. On application
pause/focus loss, PlaySession clears input and horizontal velocity; the existing server
stale-input timeout and reconciliation remain authoritative. Native QA settles two
consecutive pre-background frames before the unchanged resume/movement assertions.

Visual review at d9293fa prompted a bounded camera/composition pass: foliage has camera-only
collision on physics layer2, while player/server movement remains on layer1 and unchanged
catalog bounds. OrbitRig uses both layers; its reusable pair-framing query tests both
actors from candidate camera positions and keeps the gameplay view if none is clear.
The material paints the existing road layout onto the same flat floor, with feathered
verges and a rounded well plaza; no navigable terrain or server geometry changed.

## M1.5 item use

POST `/world/characters/{id}/items/use` accepts only item_key and expected_revision, with
Idempotency-Key. CommerceService reuses its aggregate transaction, active-encounter guard,
commerce revision and fingerprinted128-receipt map. One successful command consumes one
item and restores catalog Vigor atomically; matching retries replay, changed payloads fail,
and stale revisions reject replays after receipt pruning. Purchases and use serialize on
the same JSON/PG lock. Full-health/unowned/unsupported/active attempts do not mutate state.
InventoryRules interprets a single validated restore_vigor effect; no client amount/stat.
CharacterRecord exposes max_vigor=30 as a derived public property, not a saved field.
Existing schema1 saves need no DDL/import/reset. item_use_protocol1 is additive to server-info;
0.2.5 requires it, while world/story/folio/commerce remain1. Shop version3 invalidates old
quotes without changing existing item/listing IDs or prices. Old clients need an update
to expose Use; rollback must restore unavailable stock before serving a server without use.
The Bag keeps the same panel, search and command-recovery flow, reloads current state after
receipts and displays server-owned before/after Vigor. Preview never sends use commands.

## M1.6 authoring workflow

`tools.author_content` composes the existing immutable catalog, quest capability set and
Tidebeat engine for diagnostics, isolated examples and encounter simulations. The bundler
now exposes an import-safe function and optional root/output arguments; its default bytes
remain unchanged. No REST/WS capability, persisted field, migration or production definition
changes. `authoring/bindings.json` is production-status/binding metadata outside the runtime
catalog. It cannot grant rewards or create runtime handlers.

`tools.check_authoring` runs the real application against a copied catalog on loopback with
an independent temporary JSON store, random signing key, Godot project and XDG settings.
It imports the copied client and exercises an actual authored offer, movement, objectives,
reward and saved state. No test account touches the inherited public endpoint. Interactive
preview and automated validation share this isolation; source content is not modified.
Godot scenarios stay in the existing export-excluded tests directory. Production world
placement/dispatch remains the current modular implementation; diagnostics expose required
bindings rather than claiming arbitrary metadata can replace runtime scene integration.

## M1.7 terrain contract — implementation plan, not active runtime

The first checkpoint validates today's planar authoring inputs before catalog construction:
finite ordered bounds, capsule-clear spawn, bounded blocker/landmark lists and finite
movement parameters. Radius stays0.35 to match the existing Godot capsule and clamp.
Unknown geometry fields, including elevation, are rejected until both runtimes implement
them. The live26 definitions, scene, simulation, saves and world protocol1 are unchanged.

Next, implement one bounded height surface inside the existing world module and catalog.
Use a sparse grid of one-metre cells aligned to Dawnreef's current bounds; unspecified
cells are flat at zero. Each authored cell has four integer millimetre corner heights,
ordered southwest/southeast/northeast/northwest, split along southwest–northeast for both
height queries and Godot collision triangles. Limit each axis to128 cells and heights to
±8m for this first contract. Adjacent cells may have distinct boundary heights so stairs
have actual risers; do not smooth steps into ramps or use bilinear sampling against
triangular collision. Stable cell keys and deterministic edge tie-breaking are required.
This single-valued surface does not support stacked bridge/cave floors: those remain
separate future instance/surface contracts, not extra heights silently added to this map.

The server derives height from legal horizontal input, never a submitted position or y.
Test swept capsule clearance against existing blockers and every crossed cell boundary;
reject ascent/descent over0.30m steps and faces above the existing42-degree floor limit.
Subdivide bounded travel to at most0.10m and inspect boundary height on both sides, so a
steep face cannot become climbable by choosing very small input increments. No jumping,
fall simulation or edge teleport is introduced. Reject an unsafe move while retaining
tangential motion; camera-only foliage stays independent. Generate tops/risers and visual
route geometry from the same data; keep WayfarerController, OrbitRig and PlaySession.
A shared fixture suite must compare Python and GDScript heights, diagonal seams, risers,
cliffs, bounds and sweeps before enabling the first route. Measure vertical smoothing
without changing authoritative feet placement or accumulating reconciliation error.

Activation requires world protocol2 plus matching geometry revision/digest in the socket
auth handshake and welcome/snapshots, checked before joining. Keep axis/sequence inputs;
include authoritative y and reject unsupported position/height fields. Retain the current
session revocation, timeouts, single room, HTTP progression and receipt contracts. Keep
old clients on an explicit update message; never serve elevated geometry to protocol1.
One slope/stair route must stay outside Mara/reeds/cistern/lurker interaction approaches,
spawn and current buildings. Version the zone only when that route actually activates.

Saves retain x/z and derive y on entry from the current surface. In the first single-floor
contract a persisted y is redundant and can be stale; do not add a database column or
trust a saved altitude. Preserve safe old x/z, IDs and aggregate fields; validate bounds/
blockers and relocate only unsafe positions to the existing safe spawn, with a structured
reason. Test JSON and PostgreSQL entry/reconnect independently. Update checkpoint writes
only under the existing aggregate lock; never overwrite inventory/quest/commerce data.
The future protocol2 snapshot supplies y to both local reconciliation and remote avatars;
3D proximity must agree with the same height queries.

Roll out only after differential geometry, stale/forged packet, two-client movement,
reconnect, existing progression, PostgreSQL, rendering and Android gates pass together.
A new playable APK/version and paired backend are required at activation. Back up before
rollout; downgrade needs a validated elevated-position-to-flat relocation plan preserving
all non-location state. No public deployment or physical Device R acceptance is implied.

## M1.7 surface parity checkpoint (not activated)

`world/terrain.py` and `world/terrain_surface.gd` now implement the planned bounded
sparse surface as pure geometry helpers. They do not replace planar simulation,
WayfarerController or OrbitRig. Height and slope use piecewise planar triangles;
collision tops and two-sided interior risers derive from the same corners. Where
adjacent edge profiles cross, risers split at their intersection rather than generating
self-intersecting faces. Outer skirts are absent; future movement bounds own that limit.
Godot collision is tested with actual top and horizontal-riser raycasts, including
clockwise face winding. The Python/Godot comparison runs in CI after import.

This checkpoint proves surface queries and ray collision only. A point/ray is not a
capsule sweep and does not establish safe locomotion. Live catalog, WS protocol1,
geometry digest, saves and player feet remain unchanged. Next implement bounded capsule
sweeps/sliding against blockers, steep faces and crossed edges before protocol2 activation.
No y persistence, database migration, public deployment or physical acceptance is claimed.
