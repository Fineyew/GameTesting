# Known issues and limitations

Updated 2026-09-11. See PROJECT_STATE for current CI/artifact status.

## Release gates

- Updated public server not deployed or verified. Clients0.2.3/0.2.4 need world1/story1/folio1/commerce1;0.2.5 additionally needs item_use1.
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
- One vest vendor/equipment loop passes all M1.3 gates atde9d7a3/run34440512749. Selling,
  trading, wearable vest mesh, additional gear slots, gathering/crafting, mounts,
  housing, pets, dungeon/boss and most social features are not implemented.
  M1.5 Sunthread Bandage engineering/automated gates pass at023db75/run34550163642.
  Engineering continuation was authorized; physical acceptance is still outstanding.
- M1.4's small original art/rig/VFX candidate passes full CI/render/native validation at
  365993ce/run34483308643; actual captures and matching route frames were inspected.
  Owner art acceptance and physical-phone Device E remain open. Do not call it final.
  Two houses, distant foliage/coast/vistas, dock, cistern, lurker and most spell effects
  remain placeholders. No full audio framework/soundtrack or complete animation library.
  The sample has three clips and limited appearance tinting; it is not the full creator.
- Capsule/gravity/floor snap exist, but server movement is planar. Stairs, slopes and vertical
  authority are not tested. Full UI scaling, safe areas, left-handed controls and menu controller
  support remain accessibility work.

## Engineering

- M1.6 handoff a0b495c/run34552851591 attempt1 failed the visible gateway gate. Retained
  native10181631699 was downloaded and inspected: Pixel Launcher ANR modal covers the
  rendered game; Godot has its ready marker and no engine error. Backend/PG, Godot/API,
  authoring and render passed. The failed attempt withheld ARM64 publication. The unchanged Android rerun passes in attempt2 (native10273982286,
  build10273533063), including touch/resume. Do not treat this as a launcher ANR fix.
- M1.7 groundworkfe4551c/run34625951261 passes all full gates (148 tests/30 subtests,
  including9 PostgreSQL tests, Godot/API/render/native). It adds planar validation only.
  Shared height sampling, slope/stair
  scene, protocol2, vertical reconciliation and movement/device acceptance remain planned.

- M1.6 tools pass full CI atd1f0929/run34552020416. Structural dialogue
  reachability does not prove conditional story reachability. Existing runtime bindings
  are checked, not generated; additional NPC placements/handlers need real scene integration.
  Artifact acceptance metadata verifies references/hashes, not the truth of human review.
  Interactive desktop authoring UI and physical phones have not been manually tested here.

- Resolved M1.5 native harness issues: f761714/run34547305384 failed post-resume
  movement during an OS transition (native10179708379);0edc990/run34548765608 timed out
  on an absent legacy AppTransition field (native10180224033). Both withheld APKs.
  The API35 focused/visible/shown landscape surface parser, stable focus wait and seven
  regressions pass at023db75/run34550163642 with unchanged movement/resume thresholds.
  Exact source/retained ARM64 and inspected frame evidence are in PROJECT_STATE.
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

- M1.3 run34439273721's first Android attempt reached VT_GATEWAY_READY but failed the
  visible-gateway gate. Retained artifact10137449675 shows Android's “Pixel Launcher
  isn't responding” modal dimming the rendered game. Godot's filtered log has no engine
  error. The identical Android-only rerun cleared startup; the underlying launcher/runner
  cause remains unverified. No ARM64 artifact was published from that failed attempt.
  Keep this evidence and the unchanged assertions; do not dismiss errors to claim a pass.

- That M1.3 rerun exposed a real panel lifecycle error on Bag→vendor touch navigation:
  synchronous remove_child detached the pressed control before Godot finished input
  dispatch (can_process: !is_inside_tree). Native movement/resume completed, but the
  unchanged engine-error assertion correctly failed; artifact10137587989 retains evidence.
  GameHUD now hides retiring controls and queue_free defers their removal until the frame
  ends. GUI-dispatched mouse clicks supplement smoke coverage; native adb touch remains
  the regression for this Android path. All Godot gates now reject engine ERROR messages,
  not only SCRIPT ERROR. Fresh full CI passes atde9d7a3/run34440512749, including the
  same native touch path and visible resume; screenshots inspected. No assertions weakened.

- M1.4 candidate b5b90a5/run34478939955 passed backend/Godot/API/render but failed the
  native resume image comparison (19.35% changed, limit15%). Artifact10152976777 shows
  a small camera/position advance with no engine errors, plus a separate kit-transform
  import defect that tilted trees/well. Corrections pass at d9293fa/run34480660769: retain authored
  transforms, clear motion on application pause, and settle the pre-background capture.
  Keep the failed evidence and all movement/resume thresholds; no ARM64 was published.

- Intermediate f4ef6ec/run34480293814 failed the new geometry check because transforming
  an enclosing AABB overestimates rotated extents. It now checks transformed vertices;
  export also bakes canonical upright orientation. d9293fa passes all full gates.
  Its visual review found canopy/cast-camera occlusion. The bounded cleanup uses camera-only
  foliage and clear two-actor framing, with no movement/protocol changes. It passes full
  validation at 365993ce/run34483308643; overview/cast/native frames were inspected.
  Art acceptance and physical-device gates remain open independently.

## M1.7 surface checkpoint limits / asset candidates

Surface parity and ray collision do not prove capsule movement safety. Slopes, riser
crossings, tangential motion and protocol2 activation remain unimplemented; current
world stays flat. Initial fixture checks exposed/repaired Godot top-face winding and
trailing-newline key acceptance; no live movement was enabled during those failures.
Fal candidates are not shipped: lantern textures are three2K maps without emissive glow;
sounds need listening/loop/mix acceptance. Physical phone and art-direction acceptance
remain open. See CONTENT_GUIDE and candidate README for records and next checks.
