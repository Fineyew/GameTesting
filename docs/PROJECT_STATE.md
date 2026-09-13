# Veilbound Tides — project state

Updated 2026-09-13. Branch `feature/android-foundation`, draft [PR #4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → PROJECT_STATE → ARCHITECTURE → relevant source. Main remains bd98746; no merge/deployment.

## Current milestone

**M1.8 live creator/world appearance preview implemented and validated.**
Resumed from clean/pushed572eb62 after the interrupted conversation; no prior source
work was lost. Code `74070f3cda1489940601749dd02510cd7b49b121` passes all three jobs in
[run34769922414](https://github.com/Fineyew/GameTesting/actions/runs/34769922414). This completes the bounded creator increment; full M1.8 remains partial.

The creator and saved-character selection use one temporary isolated3D stage and
WayfarerAvatar.apply_appearance, sharing the world tint/fallback path. All nine existing
robe/skin combinations update in place without another rig. Touch drag plus
Left/Front/Right controls rotate the preview. Hidden stages stop rendering and navigation
releases the viewport. Gateway buttons allow the existing scroll container to receive
drags; retired controls defer deletion until native dispatch completes. Android safe-area
insets augment gateway margins. Startup copy now says0.2.9. IDs, assets, gameplay,
protocols, schemas and existing saves remain compatible.

CI:214 backend tests/30 subtests including10 PostgreSQL tests and both migrations;
32 terrain cases/2,067 samples/278 collision rays/17 invalid definitions/740 motions;
36 impaired-controller cases; Godot import/smoke/motion, full two-player API progression
and isolated authoring; nine Android readiness/keyboard tests; render/walkthroughs;
actual emulator install/touch/Folio/Bag/locomotion/visible-resume and native creator pass.
Creator checks cover nine choices, old/missing-ID fallback, six cached tint materials,
rig reuse, GUI/touch rotation,960x720/1600x720 framing with58px synthetic side insets,
and repeated cleanup. Real API checks reject invalid creation without losing the draft,
reload nondefault saved colors and compare the in-world rig. Native creator QA uses a
disposable loopback server and ordinary login, touch-opened menus/keyboard selection,
visible color change, touch drag/Front, creation, persisted appearance and world entry.
Local Godot smoke/API and nine Android harness tests also pass.

Verified ARM64 **0.2.9/code11**,29,165,015 bytes,
[artifact10321917205](https://github.com/Fineyew/GameTesting/actions/runs/34769922414/artifacts/10321917205); native10322236423/render10322186546,
retained through2026-12-12. Downloaded ZIP/APK CRC/SHA, ARM64-only libraries,
version/code, packaged creator scripts and retained v2/v3 signing report checked.
APK SHA256 `1e1973d26f105d37bb94cab35862f883a4bb34c68f3c8397f6b4a80c0a1ece90`;
manifest source74070f3, tested merge `2c80ce0b54828c6cabda01c7040ba1a1516da4bb`.
Inspected creator colors/rotation/saved selection, initial world entry and native resume frames.
Creator75 draw calls; town71 calls/87,774 primitives/
15,325,211 texture bytes; terrain52 calls, within existing budgets.
These are rendered samples, not physical-phone performance measurements. Debug signing
is ephemeral. A matching local backend is required for saved creator play; public
deployment, release signing, phone/thermal and owner art/motion acceptance remain open.
The native world-entry frame is transitional (camera below the scene, Connecting label).
Server logs confirm world HTTP200 and WebSocket acceptance, but this capture does not
prove a settled online camera or completed socket welcome. Full world/material/presence
checks pass separately in real Godot/API. Improve the native online-ready/camera-settled
capture before using it for online world visual acceptance; do not label this frame a
completed in-world appearance review.

Four failed candidates remain recorded below:34766994707 exposed gateway drag propagation;
34767828121 confirmed scrolling, then exposed an unconditional Back key in the native
test;34768581707 reached the creator, then exposed incorrect keyboard focus assumptions
in the color-menu test;34769314494 completed creation but exposed the Python verifier
expecting Godot's internal wrapper instead of the direct HTTP list. None published an
APK. The direct-list persistence/world contract was also checked against a local isolated
API before the final run. Text entry now replaces prefilled values
and dismisses only a visible IME. Native menu selection starts from the actual unfocused
state, covered by a real-window/PopupMenu regression. Passing evidence above supersedes
their pending status without erasing failed attempts.

Next native evidence refinement: wait for online readiness and a settled camera before
the world capture. Next bounded feature task: add/review a Run clip and Walk/Run transition through the existing
rig without changing movement authority or gameplay speed. Turn/hit/recovery clips,
foot contact, crowded-rig profiling and owner/device review still belong to M1.8.
Do not start M1.9 or broad cosmetic/content production from this checkpoint.

The subsequent handoff changes documentation only; code/build/test evidence refers to
74070f3 above. Its documentation commit uses [skip ci] to avoid rebuilding identical
runtime/tests solely for status updates. Do not describe the documentation SHA as the
APK's tested source; PR4 and Notion record both identities.

### Previous validated M1.8 motion increment

**M1.8 first motion-transition increment implemented and validated; full M1.8 remains partial.**
Local/remote avatars share horizontal-speed sampling and walk/idle hysteresis in the
existing WayfarerAvatar. Remote stair interpolation no longer speeds the gait or starts
walking from vertical correction; the old per-frame movement threshold is removed.
Cadence eases with elapsed time; existing Idle/Walk/Cast assets and cast timing remain.
Code `5972031c6771f9a29da31d8e38b4318bcc5945ad` passes all three jobs in
[run34764740003](https://github.com/Fineyew/GameTesting/actions/runs/34764740003).
Real-engine30/60/120 FPS regressions include the actual remote caller, jitter, stopping
and cast return.214 backend tests/30 subtests including10 PostgreSQL tests and both
migrations;32 terrain cases/740 motions;36 impaired-controller cases; Godot import/smoke,
full API progression/terrain/reconnect and isolated authoring;7 Android readiness tests,
render/walkthroughs and actual emulator install/touch/locomotion/visible-resume all pass.
Local Godot smoke/motion, full two-player API and authoring diagnostics also pass.
No protocol/schema/content/appearance-ID or authority change.

Verified ARM64 **0.2.8/code10**,29,156,650 bytes,
[artifact10320930156](https://github.com/Fineyew/GameTesting/actions/runs/34764740003/artifacts/10320930156),
native10320505876/render10320915177, retained through2026-12-12. Downloaded ZIP/APK CRC/SHA,
ARM64 libraries, version/code and retained v2/v3 signing report checked; updated compiled
avatar is packaged. APK SHA256 `d7991c6c4b0e9fa403bf0f125368d926b191784468f28dd1fb6ad4320140acda`;
manifest source5972031, tested merge `c198a7e5945d42b9059865eec5d23cc93de38c08`.
Inspected town/native-resume frames; town71 calls/87,774 primitives/15,182,467 texture bytes,
terrain52 calls. No new art assets or increased draw-call count. Debug signing is ephemeral;
native QA remains offline preview/navigation, not physical online/device certification.

M1.8 remains partial: new run/turn/hit/recovery clips, foot contact, creator matching,
crowded-rig profiling and owner/physical motion acceptance are not completed.
Next bounded engineering task: live creator/world avatar parity using existing choices.

### Validated M1.7 recovery handoff

**M1.7 recovery engineering validated; physical/feel acceptance remains open.**
The previous handoff7bc4e00 passes run34669910393. The paused tree was recovered intact
after workspace maintenance and pushed as code `3f2d81cf68c96a3ae3c50fefc7f2d5f1bcbb3cca`.
All three jobs in [run34763944468](https://github.com/Fineyew/GameTesting/actions/runs/34763944468)
pass. Documentation handoff `cf8bc0c38d044ce278d240279e260bfaa08a57d8` is pushed.
Its documentation-only CI rerun34764560285 was superseded/cancelled by the M1.8 push;
the full code-run evidence above remains valid, and M1.8's full run also passes.
A new deterministic network schedule
exercises the actual Godot controller against Python20Hz authority:36 combinations of
ramp/stairs/wall/terrace edge,50/150/300ms one-way delay, one-second packet silence or
rejoin. Baseline exposed15 scenarios left permanently outside3cm agreement; the .55m
moving correction dead zone also applied to resting feet. Rest now converges to1mm;
ordinary correction is capped at6m/s while existing >2m emergency correction remains.
Tests require <=3cm final error, settling within2.5s of stick release, <=.101m correction
per60Hz frame and <=2.5m peak divergence, with terrain clearance and foot-height checks.
This is deterministic controller evidence, not real cellular/physical-phone measurement.

CI passes214 backend tests/30 subtests including10 PostgreSQL tests and both migrations;
32 terrain cases/2,067 samples/278 collision rays/17 invalid definitions/740 movement
comparisons;36 impaired-controller cases; Godot smoke/full two-player progression/terrain
route/reconnect and isolated authoring. Seven Android readiness tests, both walkthroughs,
render and actual emulator install/touch/Folio/Bag/locomotion/visible-resume pass.
Maximum impairment-case peak divergence2.031m, ordinary correction0.1m/frame, final0.001m,
settling1.6s after release. These are deterministic fixtures, not measured cellular behavior.
Fresh local Godot import/smoke also passes in the recovered workspace.

Retained ARM64 **0.2.7/code9**,29,156,650 bytes,
[artifact10320225025](https://github.com/Fineyew/GameTesting/actions/runs/34763944468/artifacts/10320225025);
native10319249315/render10319288921, through2026-12-12. Downloaded ZIP/APK CRC/SHA,
ARM64-only libraries, version/code and retained v2/v3 signing report verified.
APK SHA256 `8ab9cdfc49e4a1ee3b1458cc3e4559af2aa268cd851f762ffc0f03f622c1eb1b`;
manifest source3f2d81c, tested merge `8046d27a220d6fa7a6ffbb481b8dc675db8d1a67`.
Debug identity is ephemeral. Inspected town and terrain frames:71 town/52 terrain calls,
87,774 town primitives/15,182,467 texture bytes. The label clears the avatar in this view;
it remains large over the steps and the full route is not framed. Final terrain art is open.
No protocol/schema/catalog/backend-rule/progression/saved-ID or paid-asset change.

The [Notion hub](https://app.notion.com/p/3da7c14b111981a4999dcac630171c88) is now available
with road-to-beta, owner playtest/art review and workflow pages. It is updated manually;
GitHub remains canonical. No public deployment, physical-phone test or new paid job occurred.

### Previous validated terrain activation (preserved)

**M1.7 terrain activation candidate implemented; physical/feel acceptance remains open.**
Mooring Rise is a small live Dawnreef ramp, 1.2m terrace and .3m descending steps.
Python authority and Godot prediction share bounded conservative swept-footprint traversal;
protocol2 negotiates geometry revision2/digest and snapshots server-derived altitude.
Old JSON/PostgreSQL saves retain x/z and identity; unsafe entries relocate transactionally
without resetting progression. Camera follows height; ground/riser mesh and route framing
extend the existing modular world. No new quests, rewards or asset families.

Local backend:204 tests/30 subtests pass,10 PostgreSQL tests explicitly skipped here.
Terrain parity:32 surfaces/2,067 samples/278 actual physics rays/17 invalid definitions/
740 movement comparisons pass. Code checkpoint `cd6df1dcd471a526260b2ba12e2443deb8c4a7fe`,
[run34669362714](https://github.com/Fineyew/GameTesting/actions/runs/34669362714): backend214 tests/30 subtests,
including10 real PostgreSQL tests and both migrations, pass. Godot smoke, full progression/
route/reconnect/independent altitude observer and isolated authoring pass. All three CI jobs pass.
7 Android readiness tests, render and both comparison walkthroughs pass; actual emulator
install/touch/Folio/Bag/locomotion/background-resume pass. Town:71 draw calls/87,774 primitives/
15,182,467 texture bytes; terrace frame:60 calls. Inspected town/terrace frames preserve the
visual baseline; terrain dressing/label placement remain candidate art, not final polish.

Retained ARM64 **0.2.6/code8**,29,156,650 bytes, artifact10290647152; native10289888107,
render10290322500, through2026-12-11. Downloaded ZIP/APK CRC/SHA and ARM64-only libraries
match; retained v2/v3 signing report verified (ephemeral debug identity, not a release key).
APK SHA256 `fa186966b44ddd57683253867dde086bba1271463ac4dd16d9f1a0c117507f9c`.
Manifest sourcecd6df1d, tested merge`717be09ad5d416885f0440175b45260d87c56258`.
Native gate exercises flat preview locomotion; new terrain traversal is Godot/API evidence,
not an Android route walkthrough. No public deployment, paid
asset generation or physical-phone test. Existing Fal candidates remain unintegrated.
Traversal uses an enclosing square footprint, entire touched-cell slope checks and .3m
maximum automatic step up/down; conservative corner blocking is a known feel limitation.
Do not mark M1.7 finished movement/Device R acceptance complete from these automated checks.

### Previous validated surface checkpoint (preserved)

**M1.7 surface parity implemented; full terrain milestone remains incomplete.**
Pure Python/Godot helpers now validate/query the bounded sparse height contract and
build matching top/riser triangles. An isolated CI gate compares analytic/seeded
surfaces and actual Godot collision rays. Live world remains planar: capsule sweeps,
protocol2, reconciliation/save entry and one playable route are the next checkpoint.
No catalog, WS, persistence, character controller, camera or APK version change.
Local validation:177 backend tests/30 subtests pass,9 PostgreSQL tests explicitly
skipped locally;38 new terrain regressions. Terrain parity passes31 surfaces/2,003
samples/269 actual physics rays/17 invalid definitions. Godot smoke, full existing
two-player API progression, isolated authoring,26-definition catalog/art and7 Android
readiness tests pass. Code checkpoint: `7628d305519d041f6d44b1c91f98d293ca0c49dc`,
[CI run34666830183](https://github.com/Fineyew/GameTesting/actions/runs/34666830183).
CI backend and Godot jobs pass:186 tests/30 subtests including9 real PostgreSQL tests,
both migrations, terrain parity and existing online/authoring integration. All three jobs pass, including7 Android readiness tests, actual emulator install/touch/
movement/visible-resume and render71 calls/83,630 primitives/15,182,467 texture bytes.
ARM64 artifact10289273590, native10289663087, render10289598091 are retained through
2026-12-11. Downloaded build ZIP CRC/SHA matches the artifact digest; APK CRC/hash,
ARM64-only libraries and retained v2/v3 signature report verified. APK remains0.2.5/code7,
29,152,373 bytes; SHA256 `5fb28e4459bb6669dc86d83eb0fcc3a503725d3ee57120f0cb791e06e9bc46fb`.
Manifest source7628d30; tested merge`ecb39cd27e02c34b012f42490e50238410550f8c`.
Inspected retained Dawnreef frame: existing flat visual baseline preserved. Candidates
are excluded from the APK. No new playable terrain is claimed. Initial fixture winding/newline bugs were
corrected without changing live simulation or weakening tests.

Fal evaluation sources are retained in `art_sources/candidates/fal_dawnreef_20260912`:
lantern GLB/preview, two sounds, spell headroom derivative, prompts/requests/hashes.
They are **not integrated or production-approved**. Lantern needs texture downsizing,
scale/pivot/emission/Godot/mobile checks; audio needs listening/loop/mix review and M1.9.
No new paid generation, public deployment or physical-phone test in this continuation.

### Previous validated geometry checkpoint (preserved)

**M1.7 started: planar geometry validation groundwork; full milestone incomplete.**
Reject malformed bounds/spawn/blockers/interactions, nonfinite movement values, capsule
mismatches and unsupported elevation before catalog construction. Live content, scene,
world1, saves and APK0.2.5 are unchanged. ARCHITECTURE specifies the next shared-height/
protocol2/derived-y compatibility plan; terrain runtime has not been implemented.
Code checkpoint fe4551c22c39ee6533b6e086135532a06fbd318b, run34625951261.
Backend CI passes148 tests/30 subtests, including9 PostgreSQL tests and29 geometry
regressions. All three CI jobs pass:7 Android readiness tests, Godot smoke, existing
two-player progression, isolated authored-example API preview, render and native touch/
resume. Render remains71 calls/83,630 primitives/15,182,467 texture bytes. Local139 pass/
9 PG skips/30 subtests. CI retains ARM64 artifact10274589788, native10274434937 and
render10274409949 through2026-12-10. The automatic export remains0.2.5/code7; the previously
downloaded/hash-verified owner APK below is separate evidence, not this artifact's hash.

**Reported failure assessed:** M1.6 handoff a0b495c/run34552851591 attempt1 passed
backend/PostgreSQL, Godot/API and rendering, but failed Android's visible gateway check.
Inspected native artifact10181631699 shows “Pixel Launcher isn't responding” covering
an otherwise rendered gateway; filtered Godot log has VT_GATEWAY_READY and no engine
error. ZIP SHA256:6f19916c84e80fb787d55fc57f2cb90f59d4063c462e973c01bcd19bb9f98bae.
No ARM64 artifact was published by that failed attempt. The unchanged Android job was
restarted on a fresh runner: attempt2 passes all jobs, including native touch/resume,
with unchanged source/assertions. Retained build10273533063, native10273982286 and
render10273508075 through2026-12-10. The underlying launcher ANR is not fixed.

**M1.6 authoring workflow: engineering complete.**
Code `d1f0929cd2454f923ed70279f633705d0b9af9f2`,
[run34552020416](https://github.com/Fineyew/GameTesting/actions/runs/34552020416): all three jobs passed.
119 backend tests/30 subtests include9 real PostgreSQL tests and13 authoring regressions;
7 Android readiness tests, original Godot/API and isolated authored-example integration pass.
Render71 calls/83,630 primitives/15,182,467 texture bytes; native Android install/touch/
resume passes. CI retains build10181359760, native10181360298, render10181360897 through
2026-12-10. No new APK version; the downloaded/verified playable M1.5 handoff remains below.

Tools add branch/runtime-objective/binding/asset-status diagnostics, a copied quest/dialogue
example, encounter simulation and isolated editor/client preview. Production26-definition
bundle is byte-identical. No live content, behavior, protocol, schema or art changes.
Local110 backend tests/30 subtests pass with9 PG skips; real isolated Godot/API example passes.
An initial preview assertion used the wrong response envelope and timed out; correction passes.
The interactive manual editor window is implemented but not manually visually reviewed.

**M1.5 engineering and automated validation complete. Physical acceptance remains open.**
Code: `023db7557baf173c306cd7ba711cd74628c7204b`.
[CI run34550163642](https://github.com/Fineyew/GameTesting/actions/runs/34550163642): all three jobs passed.
The owner requested continued engineering after the M1.4 device handoff. This does not
constitute physical-phone validation or owner art-direction acceptance. M1.6 authoring
workflow is complete; M1.7 has begun with content validation, not active elevation.

## Preserved checkpoints

| Milestone | Code | Handoff |
|---|---|---|
| M0 engineering | 1044f9542c1c0cda7252aa782f0b6881c5252db6 | Same checkpoint |
| M1.1 story | 4efd3a689d93e2ed2fa31647a2ff67affca67c5e | d1382147f3b88388c461abcb99506c28e3da3771 |
| M1.2 acquisition/folio | d0c604894ba768c6647b42ff19a76285d0e41bce | 56370e6dd442485101824dc188d12e00aa87d3f8 |
| M1.3 vendor/equipment | de9d7a38bed6c18b396173cfd926c09c20e8159d | 3ac1f8fc69379b15594191294e6248e9911be950 |
| M1.4 visual candidate; acceptance open | 365993ce7e79fc29025ee23d1c77cbf449ad2bfc | a5d06dbaa819b25897dbf08f632ce962dd74db58 |
| M1.5 engineering; physical acceptance open | 023db7557baf173c306cd7ba711cd74628c7204b | 4bcecfec418d4907bcfc4cf9571c78c1a026c048 |
| M1.6 authoring tools | d1f0929cd2454f923ed70279f633705d0b9af9f2 | a0b495c4f55719b2c8379daf584a8efb22e847c4 |

M1.5 documentation handoff4bcecfe/run34551125125 also passed all three CI jobs.
Roadmap checkpoint edec97b preserved history and introduced progressive whole-game art production.
M1.4 code run34483308643 and handoff run34484981552 both passed. Its prior ARM64
0.2.4/code6 artifact10154911714 remains historical evidence; current deliverable is below.

## What works / latest changes

- Modular Godot4.5.1 gateway/creator, touch/WASD/controller movement, orbit/recenter,
  offline preview, interpolation/reconnect, preset chat, inventory/search/settings/appearance.
- Server-owned Tidebeat/intents/Focus/rewards, five authored quests, Mara's branching story,
  investigation/three spell lessons, six obtainable spells and persistent 1–6 spell folio.
- Mara's supply cart sells the existing vest for12 earned shell chits; one chest slot,
  catalog Guard1 per incoming hit, comparison/equip/unequip, separate appearance.
- **M1.5:** buy the existing Sunthread Bandage for5 chits; use one from the Bag outside
  combat to restore up to12 Vigor, cap30. Full-health/active/unowned/forged attempts cannot
  consume supplies. Bag shows health, effect, ownership and before/after preview.
  Server failures reach the existing retry/reload UI; stale use leaves saved state unchanged.
- Healing, consumption and exact-command receipts commit atomically through existing
  commerce revisions and JSON/PostgreSQL aggregate locks. Concurrent use/purchase cannot
  race; old receipts/revisions prevent duplicate consumption. No new persisted fields/DDL.
- Shop version3 enables existing stock. Derived max_vigor=30 and item_use_protocol1 are
  additive; existing world/story/folio/commerce1, IDs, schema1 saves and26 definitions remain.
- M1.4 original eight-piece Lantern Well/cart kit, 13-bone Wayfarer/Mara Idle/Walk/Cast,
  shared tints, Glimmer anticipation/travel/impact and saved short/no-camera-cut option.
  Camera-only foliage stays separate from movement; pause clears input/velocity.

## Historical M1.5 validation / APK (current evidence above)

At023db75: **106 backend tests /30 subtests**, including **9 real PostgreSQL tests** and
both migrations. Content and art budgets pass. **7 Android readiness regressions** pass.
Strict Godot import/smoke and actual two-player Godot/API progression pass, including
buy/use/capped healing/reconnect and stale-use server feedback/reload without mutation.
Local:97 backend passed/9 explicit PG skips/30 subtests; Godot/API and seven readiness tests pass.
Two upstream backend deprecation warnings remain.

Actual render: **71 draw calls /83,630 primitives /15,182,467 texture bytes**, within
unchanged150-call/150k/128MiB gates. Matching routes retained; Movie Maker FPS is not a
performance measurement. Native API35 x86_64 install, gateway, Folio, Bag→vendor touch,
movement, visible landscape resume and repeat movement pass without engine errors.
Resume difference0.00619 (<0.15); repeat movement0.48249 (>0.025). Frames inspected.
The readiness harness waits for a focused, shown landscape surface with no rotation animation;
it sends only one post-resume swipe. Native uses preview; actual online use is tested separately.
The item-use screenshot is a server-shaped UI fixture, not a claim of native online progression.

Verified ARM64 **0.2.5/code7**, **29,148,100 bytes**, minimumAPI24/target35.
Build artifact **10180711026**, native **10180711956**, render **10180713027**; CI retention
through2026-12-10. Manifest source023db75; tested merge`b8b67a2f3036b93adc1e416de14bbb5d37c78a71`.
SHA256`6e9ad8c7a15dbd210e886bc3e265daa538ee1f693232d310b4df8524ee286152`.
ZIP/APK CRC/hash, ARM64-only libraries, version/code, packaged scripts and retained v2/v3
signature report verified. APK, Bag capture and evidence ZIP saved for owner handoff.
Ephemeral debug signing is not a release/update identity. No public backend update occurred.

Earlier f761714/run34547305384 failed native resume touch during an OS transition;
0edc990/run34548765608 failed closed on an absent legacy window field. Both retained
failure evidence and withheld APK publication. Actual API35 surface parsing plus regressions
passes at023db75; KNOWN_ISSUES/CHANGELOG retain the failed attempts.

## Placeholder / unverified / next

**All physical ARM64 phone validation and owner art acceptance remain unverified.**
Other houses, distant trees/coast/vistas, dock, cistern/lurker, most VFX, all audio, full
animation/creator, wearable vest mesh and broader UI/accessibility remain unfinished.
Server movement now follows the bounded Mooring Rise surface. No additional quests/spells/regions, co-op/dungeons, selling,
trading, gathering/crafting, mounts/housing/pets or broad social content were added.
Recovery/moderation, load tests, JSON→PG import/restore, staging/production, signing and
updater remain future work. One process owns the room;32-player cap is unbenchmarked.

**Next engineering: M1.8 live creator/world avatar parity**, scoped in ROADMAP.
Reuse the existing three robe/three skin choices and Wayfarer scene; preserve saved IDs
and current form/navigation. No new cosmetic families or gameplay systems in that checkpoint.
The deterministic M1.7 delay/silence/rejoin gate now passes. Preserve its correction/settling
assertions and obtain Device R evidence before calling finished movement accepted. Physical
edge/corner/stair feel, variable-rate/jitter/long-outage behavior and the full-route visual
review remain open. No broad creator, asset-family or content production increment yet.
Current tools cover catalog templates/diagnostics, scene/asset binding/status checks and
an isolated authored preview example. No bulk live content. Keep M1.4/M1.5
Device E open alongside engineering; README provides local backend/USB reverse testing.
The inherited public endpoint has not been updated or verified.

## Build / continue

Install backend/requirements.lock; run pytest backend/tests, tools.build_catalog,
tools.check_art, tools.author_content check, tools.check_godot, tools.check_terrain,
tools.check_movement_network, tools.check_online and
tools.check_authoring with GODOT_BIN set to4.5.1.
Android job adds Pillow11.3.0 and unittest discover -s tools/tests. CI supplies PG16,
JDK17/SDK35/templates, render and emulator. README has exact commands and phone checklist.
Source: backend/app/modules, content, godot_project/scripts, art_sources, tools, infra.
Preserve dependency injection, content IDs, aggregate locks/receipts and deferred HUD deletion.

### Creator native validation correction (2026-09-13)

Initial code9ed2a71/run34766994707 passes214 backend tests/30 subtests, PostgreSQL,
full Godot/API/authoring/terrain/network, render and walkthrough gates. Creator75,
town71 and terrain52 draw calls pass. Inspected coral/tablet/wide/selection frames.
Native existing movement/Folio/Bag/resume passes, then new creator QA times out revealing
Server connection after a swipe. No ARM64 artifact was published; retained native
10320098524 and render10320063696 preserve the failed attempt.
Gateway buttons use the engine's STOP mouse filter, blocking emulated touch-drag input
from reaching the ScrollContainer. The correction uses PASS only for gateway buttons;
the existing scroll container owns scrolling and cancels the press on drag. A GUI-input
regression requires propagation and no accidental offline entry. Native QA additionally
waits for a focused, stable window after its deliberate restart and captures failures
before cleanup changes the screen. Existing thresholds are preserved. Fresh CI required.
### Native creator text-entry harness correction (2026-09-13)

Codef04a8e6/run34767828121 passes backend, Godot/API, render and walkthrough gates;
the emulator confirms the scroll correction reaches Server connection. The new creator
harness then sends Back while the hardware-keyboard emulator has no visible IME,
returning to the launcher before login. This is a harness navigation failure, not a
creator render failure. Native10321285952/render10320904717 retain that failed attempt;
no ARM64 artifact was published. Text entry now selects/replaces prefilled values and
sends Back only when API35 reports the IME visible. Nine local Android harness tests
pass, including hidden/visible keyboard cases. Full native validation is still required.
### Native creator menu-focus correction (2026-09-13)

Code3ae529b/run34768581707 passes backend, Godot/API, render and walkthrough gates.
Native checks now successfully scroll, replace the server URL, log in and display the
creator. The color-menu test stops because a touch-opened Godot PopupMenu has no
keyboard-focused item: one Down then Enter reselects the first item. Native10321610947
and render10321895459 retain the failed attempt; no APK was published. The harness
now sends two Down presses before Enter. A real-engine regression opens the actual
OptionButton, confirms focus=-1, delivers those keys through the root window and
requires the second item and visible appearance callback. Corrected local smoke and
nine Android harness tests pass. Full native validation is still required.
### Native creator HTTP-response correction (2026-09-13)

Codeeed92ed/run34769314494 passes backend, Godot/API, render and walkthrough gates.
Native creator color changes, touch rotation, Front reset, name entry, creation and
saved-character preview now succeed; inspected colors/saved frames are readable. The
last Python persistence check incorrectly expects Godot ApiClient's internal data
wrapper from the direct HTTP response, whose documented route returns a raw list.
Native10322040539/render10321960606 retain the failed attempt; no APK was published.
The harness now indexes the actual list. A local isolated real-API check confirms
creation, raw-list reload, coral/deep persistence and world entry; nine harness tests
also pass. Final complete native validation remains required.
