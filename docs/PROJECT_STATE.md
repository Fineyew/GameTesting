# Veilbound Tides — project state

Updated 2026-09-10. Branch `feature/android-foundation`; draft PR [#4](https://github.com/Fineyew/GameTesting/pull/4).
Read README → this file → ARCHITECTURE → relevant source before editing.

## Current checkpoint

**M0 engineering complete** at `1044f95`. **M1.1 complete**: one narrow quest/dialogue
framework increment, code/APK source `4efd3a689d93e2ed2fa31647a2ff67affca67c5e`.
This handoff changes documentation only. Main remains at `bd98746`; no merge/deployment.
Restoration is finished; never restart it or replace the working architecture.

## What works

- Godot 4.5.1 modular gateway/creator, appearance/affinity, third-person movement, orbit/
  collision camera, touch controls, procedural Dawnreef, inventory search and settings.
- Argon2 accounts with legacy hash upgrade, versioned access sessions/revocation/renewal.
- Real server-authoritative WebSocket presence/movement, interpolation/reconnect and preset
  chat. One process/room, 32-player cap unbenchmarked; world protocol 1 is unchanged.
- Persisted Tidebeat turns, intents, Focus and transaction/retry-safe combat rewards.
- JSON development and PostgreSQL adapters; migrations 0001/0002 preserve original tables.
- **M1.1:** catalog-owned dialogue branches/conditions, persisted server cursors, NPC quest
  offers, ordered defeat/inspect/talk objectives and once-only XP/item/currency rewards.
  New dialogue/inspection APIs check ownership, live proximity and combat state.
- Mara's original first quest plus **An Answer in the Reeds**: listen at reeds, then the
  sealed cistern, then return for 40 XP/5 chits. HUD/journal use objective data. Two quests,
  one enemy, three learned spells; three more functioning definitions lack acquisition.
- Server advertises `story_protocol=1`; client 0.2.1 checks it before login. Original starter
  compatibility APIs remain. Old saves load with an empty optional dialogue cursor.

## Tested evidence and Android artifact

[CI run 34431891977](https://github.com/Fineyew/GameTesting/actions/runs/34431891977) at
`4efd3a6`: **all three jobs passed**. 38 backend tests, 27 subtests, actual PostgreSQL and
both migrations; Godot import/smoke plus real account→creation→two-player presence→
branching dialogue→combat→reconnect→ordered investigation→persistent once-only rewards.
Local:35 passed, 3 PostgreSQL tests explicitly skipped; Godot smoke/online also passed.

Android: signature-verified ARM64 debug APK **0.2.1/code 3**, 27,897,336 bytes, minimum
API24/target35. Artifact **10134809705**, runtime evidence **10134860798**, retained until
2026-12-09. Manifest source `4efd3a6`; tested PR merge tree `7df73d1`.
SHA-256: `f939748c4db5337c1835acb568be78281925287e7902f9517ac886402fbce5e9`.
The downloaded APK hash/manifest/ARM64 ABI/version and included M1 catalog were checked.

API35 x86_64 emulator passed install, visible gateway, touch preview/locomotion,
background/resume with visible world and repeat touch movement. Screenshots inspected;
no engine/shader errors. Native emulator coverage is exploration/resume; the full online
story is verified with Godot/API integration, not a physical phone. Fresh desktop render:
**87 draw calls**, default shadows off. Coastline overlap and landscape orientation fixed.

M0 history: run 34424981946 at 2101aa4 passed initial gates; stronger visible-resume run
34430377236 at 69457a4 passed before checkpoint 1044f95. Original 0.2.0 artifact 10132315403
remains retained; source and history are preserved. See CHANGELOG for the milestones.

## Unverified / placeholder / planned

Physical S25 Ultra/ARM64 install/touch/safe areas, 20-minute performance/thermal/memory/
battery measurements and cellular/Wi-Fi transitions remain **unverified release gates**.
The updated public host is not deployed/verified; online play needs this branch's backend.
README gives the local-server/USB-reverse and physical-device procedure. No release signing.

Procedural art, simple gait/VFX and flat terrain remain placeholders; no finished audio.
Folio editing/spell acquisition, equipment/vendors, harvesting/crafting, mounts, housing,
pets, dungeons/bosses, free chat/moderation and full account recovery/refresh lifecycle
remain unfinished. Collect-item/repeatable quest execution and additional NPC visual
bindings are future work. Existing JSON→PostgreSQL import/restore drills remain release gates.

## Next / build and test

Next is ROADMAP M1.2: make existing additional spells obtainable and add validated folio
selection. No bulk quest/spell/world production. Preserve M0 and M1.1 behavior/tests.

`python -m pip install -r backend/requirements.lock`; `python -m pytest backend/tests -q`;
`python -m tools.build_catalog`. Set GODOT_BIN to 4.5.1; run `python -m tools.check_godot`
and `python -m tools.check_online`. CI supplies the migrated PostgreSQL test service and
SDK35/JDK17/export templates; README documents Android export/runtime commands.

Key paths: `backend/app/modules/{vertical_slice,quests,combat,world}`, `backend/app/db`,
`backend/tests/test_story_progression.py`, `content`, `godot_project/scripts`, `tools`,
`.github/workflows/foundation.yml`. Follow existing injected ports and aggregate transactions.
