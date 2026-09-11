# Veilbound Tides — project state

Updated 2026-09-11. Branch `feature/android-foundation`, draft [PR #4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → PROJECT_STATE → ARCHITECTURE → relevant source. Main remains bd98746; no merge/deployment.

## Current milestone

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

## Tested / retained APK

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
Server movement is planar. No additional quests/spells/regions, co-op/dungeons, selling,
trading, gathering/crafting, mounts/housing/pets or broad social content were added.
Recovery/moderation, load tests, JSON→PG import/restore, staging/production, signing and
updater remain future work. One process owns the room;32-player cap is unbenchmarked.

**Next: continue M1.7 terrain authority.** Prove Python/Godot height and collision parity
against shared fixtures before activating protocol2 and the first slope/stair route. Preserve flat saves,
server movement authority and the existing player/camera modules.
Current tools cover catalog templates/diagnostics, scene/asset binding/status checks and
an isolated authored preview example. No bulk live content. Keep M1.4/M1.5
Device E open alongside engineering; README provides local backend/USB reverse testing.
The inherited public endpoint has not been updated or verified.

## Build / continue

Install backend/requirements.lock; run pytest backend/tests, tools.build_catalog,
tools.check_art, tools.author_content check, tools.check_godot, tools.check_online and
tools.check_authoring with GODOT_BIN set to4.5.1.
Android job adds Pillow11.3.0 and unittest discover -s tools/tests. CI supplies PG16,
JDK17/SDK35/templates, render and emulator. README has exact commands and phone checklist.
Source: backend/app/modules, content, godot_project/scripts, art_sources, tools, infra.
Preserve dependency injection, content IDs, aggregate locks/receipts and deferred HUD deletion.
