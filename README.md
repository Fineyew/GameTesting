# Veilbound Tides

An original Android-first online fantasy RPG built with Godot 4.5.1, FastAPI,
PostgreSQL, Docker and Nginx. Continue this repository; do not recreate working systems.
The active work is `feature/android-foundation`, [draft PR #4](https://github.com/Fineyew/GameTesting/pull/4).

## Start here

Read [PROJECT_STATE](docs/PROJECT_STATE.md), [ARCHITECTURE](docs/ARCHITECTURE.md),
[GAME_DESIGN](docs/GAME_DESIGN.md), [ROADMAP](docs/ROADMAP.md), [CONTENT_GUIDE](docs/CONTENT_GUIDE.md),
[DECISIONS](docs/DECISIONS.md), [KNOWN_ISSUES](docs/KNOWN_ISSUES.md) and [CHANGELOG](CHANGELOG.md).
M0 engineering is complete: PostgreSQL/Godot integration, retained signed ARM64 export,
inspected renders, and Android emulator touch/visible-resume checks pass. Physical phone
validation remains unverified. M1.1, M1.2 and M1.3 are complete: reusable story rules,
Mara's investigation/three earned spells, a persistent folio, and one earned vendor/equipment loop.
M1.4 is an implemented visual benchmark candidate at
`365993ce7e79fc29025ee23d1c77cbf449ad2bfc`.
[CI run 34483308643](https://github.com/Fineyew/GameTesting/actions/runs/34483308643)
passes 90 tests / 30 subtests with PostgreSQL, full Godot/API progression, a 71-draw-call
render sample, matching walkthrough recordings and Android touch/visible-resume checks.
Verified ARM64 **0.2.4/code6** is retained as artifact **10154911714**. PROJECT_STATE records
exact source/manifest/APK hashes and evidence. Owner art-direction acceptance and the
required physical-phone baseline remain open. The owner authorized continued engineering;
M1.5 now has a bandage-use candidate awaiting full CI and a fresh APK. See PROJECT_STATE.

## What is playable

Create an account and one Wayfarer with appearance/affinity; enter a small original
Dawnreef with a small authored Lantern Well/Mara art benchmark; move with touch/WASD/controller stick; orbit/recenter the camera;
see other connected players and use preset chat; follow Mara's branching dialogue, accept the first quest,
fight the Fog-Thorn Lurker in server-owned Tidebeat turns and retain XP, currency and
inventory rewards. Then trace a note through the reeds and sealed cistern entrance and
return to Mara for a once-only reward. Continue three short lessons to earn Beacon Trace,
Reed Aegis and Seam Lance; choose 1–6 learned spells in the Folio before combat. Buy the Lanternkeeper Vest from Mara’s supply cart for 12 earned shell chits, compare
its +1 Guard and equip/unequip it through the Bag. It reduces each incoming Tidebeat hit
by one while leaving robe appearance unchanged. Shopping requires proximity to Mara;
equipment changes require no active encounter. Bandages cost five shell chits; use one from the Bag outside combat to restore up to12
Vigor, capped at30. Full-health attempts consume nothing. Resume an active encounter after reconnecting. Search the bag and
change FPS, shadows and render resolution. Offline exploration is explicitly a preview
with no saved progression. The sample area now uses original editable environment pieces,
animated Wayfarer/Mara rigs and a confirmed Glimmer Spark sequence. Settings can shorten
spell effects and remove the camera cut. This is not yet the complete 18-quest authored vertical slice.

The legacy `scenes/vertical_slice_client.tscn` and its script are preserved. The active
main scene is `godot_project/scenes/app/bootstrap.tscn`; older deployment documents'
legacy interface descriptions do not describe this new client.

## Local development

Python 3.12 and Godot **4.5.1 stable** are the tested versions. From repository root:

```bash
python -m venv .venv
# Activate .venv using your shell's normal activation command.
python -m pip install -r backend/requirements.lock
python -m tools.build_catalog
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Local mode defaults to JSON saves at `var/vertical_slice_save.json`, ignored by Git.
Open `godot_project/project.godot` and press Play. Under **Server connection**, set
`http://127.0.0.1:8000/api/v1`. HTTP is permitted only for localhost in editor/debug builds;
shared servers require HTTPS. The inherited default `https://game.surveyroute.work/api/v1`
has not been updated or verified operational in this session. World protocol 1, story protocol 1 and folio protocol 1 and commerce protocol 1 are required; the backend needs
the M1.5 update and item_use_protocol1 before this client signs in.

To test an attached Android phone against your PC server, install the APK, run
`adb reverse tcp:8000 tcp:8000`, and use the same localhost URL. This is a development
recipe; physical phone results are recorded separately in PROJECT_STATE.

## Checks

```bash
python -m pytest backend/tests -q
python -m tools.build_catalog
# Set GODOT_BIN to your Godot executable, or put `godot` on PATH.
python -m tools.check_art
python -m tools.check_godot
python -m tools.check_online
```

`check_online` starts an isolated API and another WebSocket player, then runs the real
Godot account/creator/movement/quest/combat/reward/reconnect flow. Unit tests alone are
insufficient. PostgreSQL tests explicitly skip unless `VT_TEST_DATABASE_URL` names an
isolated database migrated to head. CI runs both migrations and the PostgreSQL tests.

## Android build and runtime checks

Use the checked-in **Android** export preset: ARM64, INTERNET permission, app ID
`work.surveyroute.veilboundtides`, version 0.2.5/code 7 (candidate; check validation status in PROJECT_STATE). Use Godot 4.5.1 export templates,
JDK17, Android SDK platform35 and build-tools35.0.0. See the
[official engine export instructions](https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_android.html).
The exported engine minimum is API24, target API35; minimum OS is not a device-performance guarantee.

The Linux/CI helper requires `GODOT_BIN`, `ANDROID_HOME`, `JAVA_HOME` and installed templates:

```bash
python -m tools.export_android --emulator
xvfb-run -a python -m tools.check_render
# With an Android emulator already booted and adb available:
python -m tools.check_android
```

The build script creates the ARM64 deliverable, a separate x86_64 QA APK, signature
verification reports and a SHA-256/source-commit manifest. Only the ARM64 file is for
phones. CI retains it as `veilbound-tides-android-foundation` with render evidence;
`android-runtime-evidence` records emulator touch/resume checks. Artifact retention
is 90 days. `dawnreef-render-evidence` also retains captures on failure. Debug keys are ephemeral; a differently signed later test APK can require
uninstall/reinstall. Release signing and Play Store/AAB publication are not configured.

### Physical phone handoff (still unverified)

For the M1.4 visual review, spend 2–3 minutes on the existing route: enter preview,
walk from the arrival path to the Lantern Well, orbit the floating lens and Mara, then
walk west toward her supply cart. Check the avatar in motion, tree/roof silhouettes,
paving and readable HUD. The retained before/after MP4s use matching controls/cameras
at .75 render scale with shadows off (30.83 seconds each); they are Movie Maker captures, not measured FPS.
On an online test character, cast Glimmer Spark, try **Short spell effects · no camera
cut**, then revisit Mara's vendor/Bag flow. These are existing progression rules.
Owner art-direction acceptance and the real-phone measurements below are still open;
M1.4 cannot be marked complete from desktop/emulator evidence alone.

The owner's Galaxy S25 Ultra has not been available to this workspace. Install the
**ARM64** APK from the successful CI run recorded in PROJECT_STATE; compare its SHA-256
with `build-manifest.json` (`Get-FileHash <apk> -Algorithm SHA256` on Windows).
With Android platform-tools and USB debugging enabled:

```bash
adb devices
adb install -r veilbound-tides-0.2.5-android.apk
adb reverse tcp:8000 tcp:8000
```

Run the local backend above, select **Server connection** →
`http://127.0.0.1:8000/api/v1`, create a test account and character, and complete Mara's
quests and spell lessons while a second client is connected. Save a folio, reconnect,
and verify that only prepared spells appear in combat. Buy the vest with quest-earned
chits, compare/equip it, reconnect, verify the saved balance/equipment and test Guard in
combat; unequip it and confirm that robe appearance stays unchanged. Buy and use one
bandage while injured; verify Vigor/inventory after reconnect and no consumption at full health. Verify touch movement/camera, landscape,
readable menus, cutout/navigation safe areas, reward persistence after sign-in, and
reconnect after backgrounding. Test cellular/Wi-Fi switching against an accessible
HTTPS test server separately; USB reverse does not simulate a mobile network.

Record device model/OS, source SHA/APK hash, quality preset, failures and logs. A 20-minute
30 FPS session must measure frame pacing, memory (target 700 MB working/under1 GB peak),
thermal throttling and battery use; measure network bandwidth and reconnect behavior.
Desktop render observations do not establish these phone measurements.
Use `adb logcat -d -s godot:V AndroidRuntime:E` for engine failures; scrub user data before
sharing logs. Do not run `tools.check_android` on a personal phone: it changes emulator
display/test-profile settings. Physical results stay open until actually recorded.

## PostgreSQL and deployment

Important variables: `VT_PLAYER_STORE` (`json` or `postgres`), `VT_DATABASE_URL`,
`VT_VERTICAL_SLICE_SAVE_PATH`, `VT_ENVIRONMENT`, `VT_JWT_SECRET`, `VT_DEBUG`.
Full defaults and validation are in `backend/app/core/config.py`. Staging/production
require non-placeholder secrets and PostgreSQL. Never put a production secret in the client.

Back up existing saves before switching persistence. Migration 0002 adds the runtime
state table and session version column; it does not import JSON players automatically.
Existing JSON accounts need an explicit validated import preserving IDs and balances.
Do not erase the old volume or switch a live service without testing backup/restore.

```bash
python -m alembic -c backend/alembic.ini upgrade head
# Copy infra/.env.example to infra/.env and supply credentials/TLS files first.
docker compose --env-file infra/.env -f infra/docker-compose.yml up --build
```

Nginx needs `infra/certs/fullchain.pem` and `privkey.pem`; HTTP redirects to HTTPS.
Run **one** application process: the world room is currently process-owned. No production
update has been deployed here. Historical runbooks remain under `docs/deployment/`;
follow the current persistence and protocol requirements before using them.

## Repository map

| Path | Responsibility |
|---|---|
| backend/app/modules | Gameplay/service modules; boundaries checked by tests |
| backend/app/db, backend/alembic | Persistence adapters and additive migrations |
| content | Validated source gameplay definitions |
| godot_project | Modular scenes, scripts and generated catalog |
| art_sources | Editable Blender scenes, original recipes and benchmark status/budgets |
| tools | Catalog/art validation, Godot integration, Android export and runtime checks |
| .github/workflows | Repeatable CI checks and retained artifacts |
| infra | Existing Docker/Nginx/backup setup |
| docs | Canonical state, design, authoring, decisions and historical plans |
