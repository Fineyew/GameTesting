# Veilbound Tides — authoritative game direction

Original Android-first fantasy MMO/RPG. This continues Auralis, Dawnreef, Mara and the
existing content identity; it does not introduce a replacement game. Implementation
status is in PROJECT_STATE. Unless marked implemented, the experiences below are targets.

## Fantasy, world and conflict

Become a Wayfarer whose Veilmark hears the conversation between living magic and ancient
Vey mechanisms. Auralis is a world of floating reefs above the Glimmerdeep. Lantern Wells
keep those reefs steady. Discover distant places, collect magic through memorable quests,
make friends, and gradually build a persistent personal life in the world.

The starter region is Dawnreef Atoll: warm stone buildings, woven reeds, teal roof forms,
lantern-lit commons, mooring paths and fog-thorn margins. Mara Lanternwright tends the
well with practical care. Its light begins answering something beneath the reef. The
lurker is drawn to that disturbance; defeating it helps the town but does not explain
the voice. The sealed Saltglass Cistern points toward the first major investigation.

Target subareas: Lantern Commons, reed terraces, fog-thorn margins, mooring walk, and
Saltglass Cistern. Current Dawnreef is a small flat engineering scene with landmarks;
these names do not mean five finished environments exist.

## Magical disciplines

| Discipline | Philosophy | Strategic possibilities | Visual direction |
|---|---|---|---|
| Lanterncraft | Understanding creates openings | Reveal, mark, precise focused strikes | Lenses and orbiting warm lights |
| Rootbinding | Relationships hold ground | Bind, guard, sustain allies | Living threads and branching knots |
| Tideseaming | Redirect pressure | Mend, transfer, stagger effects | Curved seams and layered arcs |
| Glassweaving | Store and release a moment | Charge, refract, delayed bursts | Faceted planes |
| Echocalling | Actions leave useful traces | Delayed repeats and tempo | Repeating rings and silhouettes |
| Weightkeeping | Choose what must remain | Anchor, absorb, sacrifice for control | Suspended stones and weighted glyphs |

The first three affinities exist in the creator, but currently all learn the same
three starter spells. Cross-training, affinity-specific progression and the other
traditions remain planned. Spells should come from instructors, exploration, quests,
bosses and crafting; important spells should have stories, not gambling-based acquisition.

## Tidebeat combat and core loop

Implemented folio: prepare 1–6 distinct learned spells, all available without a random
hand draw. Brace/Gather are universal and use no slots. Preparation is locked during an
active encounter. New spells enter the learned collection, not the prepared folio.
Old saves prepare their already-known spells automatically, without granting new ownership.
A beat resolves the player's chosen action, the visible enemy response, then upkeep.
Start with 3 Focus; regenerate 1 per beat, cap 6. Brace absorbs 6 incoming damage;
Gather adds 2 Focus before upkeep. Intent knowledge, resource use and preparation matter.

Implemented: Glimmer Spark (8 damage/1 Focus), Root Snare (6 damage and bind4/2 Focus),
Tide Mend (heal8/2 Focus; never secretly attacks). Additional functioning definitions:
Beacon Trace (mark next damage +6), Reed Aegis (guard10), Seam Lance (damage15/4 Focus).
All six are now obtainable. After An Answer in the Reeds, Mara offers three short lessons:
Reading the Afterlight (inspect the sealed cistern, return: Beacon Trace), What the Reeds
Hold (study reeds, return: Reed Aegis), and A Measured Release (cast Beacon Trace, meet a
10-damage intent with Reed Aegis, finish the lurker encounter, return: Seam Lance).
Each lesson grants its named spell once, with no added XP/currency payout. Practice can
span encounters; only successfully resolved casts count. The cistern remains sealed. Marks cap at 12; guard
and bind currently affect the immediate response. The lurker has 32 Vigor and cycles
4-damage,10-damage,0-damage announced intents. Defeat restores the player at the well;
a 50-beat cap bounds stalled fights. Server transactions own outcomes and rewards.

Explore shared space → meet a character/discover a phenomenon → choose a quest/activity
→ prepare spells → solve a tactical encounter/puzzle → earn a specific reward → change
build/appearance → return to a social home → follow another lead. Future cooperative
combat needs participant ownership, ready timers and reconnect rules before implementation.

## First supplies and equipment (M1.3 implemented and tested)

Mara's existing Dawnreef Supply Cart sells one Lanternkeeper Vest for 12 shell chits.
The first quest plus lurker victory yields 14, so the purchase follows helping the town.
One owned copy, one chest slot, level 1 requirement. The vest's existing additive Guard1
reduces every incoming Tidebeat hit by one, stacking with Brace/bind/spell protection
and clamping damage at zero. This changes survivability, not Focus, spells or movement.
Compare current/candidate Guard before buying or equipping; no random stat rolls.

Buying puts the vest in the bag; equipping is explicit. Unequipping keeps ownership.
Equipment changes are blocked during encounters. Stat equipment uses the existing
`equipment` map; visual identity stays in `appearance` and is never overwritten by gear.
The vest does not yet have a finished wearable mesh, and full cosmetic overrides/transmog
are future work. Existing bandage stock is visible but unavailable until item use works;
no selling, trading, crafting or additional gear categories are introduced in this increment.

## First hour target

| Time | Experience | Purpose |
|---|---|---|
| 0–5 min | Startup/account/compact creator | Personal identity and reliable connection |
| 5–12 min | Arrive, explore, meet Mara and nearby players | Movement, interaction, place |
| 12–20 min | First lurker encounter | Intent, Focus, healing and defense |
| 20–30 min | Investigate a reed phenomenon | Magic outside combat |
| 30–40 min | Return and earn a spell; change folio | Memorable acquisition and preparation |
| 40–50 min | Help a resident in another neighborhood | Local culture and a meaningful side quest |
| 50–60 min | Open the cistern investigation | Agency and a larger mystery |

The account/creator/exploration/first combat quest and one short Mara investigation are
implemented, followed by the three small spell lessons above. An Answer in the Reeds sends the Wayfarer to listen at two existing landmarks
and return; it awards 40 XP/5 chits once. The cistern remains sealed. There is not yet an
hour of authored content. Quests should frequently teach ecology, characters,
locations or mechanics, instead of repeatedly asking for arbitrary kill totals.

## Art, UI, audio and performance

Original stylized silhouettes and colorful, restrained materials: teal/coral/warm
stone and luminous reeds; cool distant reefs. UI uses dark teal, cream type and gold
primary actions, large touch targets and scrollable panels. Camera orbit and movement
have separate thumb areas. Recenter and battery settings are accessible. Procedural
models, primitive VFX and simple gait are explicitly placeholders for replaceable scenes.

Target 30 FPS sustained on representative 6 GB Android hardware, optional 60 high tier;
700 MB working memory/under 1 GB peak;150 draw calls typical/250 dense;150k visible triangles
baseline;128 MB initial texture budget; base download under150 MB. Room cap 32 and 15 KB/s
per-player network target require measurements, not assumptions. Test 20-minute thermal
sessions and background/network transitions on actual phones. Settings currently expose
FPS, shadows and render scale; LOD, view distance, effects and UI/accessibility scaling
remain future work. Audio buses/music/ambience/SFX/subtitles remain planned.

## Authored slice specification and expansion

M1 target: one town plus adventure region; 18 varied quests; 18 obtainable usable spells
across three initial traditions; 8 recurring NPCs; 5 regular enemy types; one handcrafted
dungeon with puzzle/checkpoint/phased boss/recognizable loot; equipment/vendor and
persistent progression; an earned mount; two gatherables/recipes if core stability holds.
Housing proof of concept follows core gates. See ROADMAP for sequencing.

Long-term vectors: character and discipline progression, spell collection, cosmetics,
mounts, housing trophies, crafting, exploration and social accomplishments. Separate
appearance from stat equipment. Useful source-driven loot, no flood of junk. Shared
towns/wilderness coexist with private encounters/interiors/dungeons/housing instances.
Friends, parties, guilds, trading, minigames, pets and events remain planned. Android
is the primary product; Windows then iOS share backend/content/account state.

No monetization is implemented. Avoid pay-to-win, child-targeted gambling, forced ads
and deliberate misery sold away as convenience. Inspiration stays at broad genre
principles; review every new name, creature, region, spell and asset for originality.

## M1.4 art benchmark candidate

The small Lantern Well/Mara area tests warm limestone, woven teal canopies, curved sail
roofs, brass lens details and tapered reed foliage within the established Dawnreef palette.
The Wayfarer has a split travel coat, short mantle, folio satchel and lens staff; Mara has
her own lanternwright apron, tools and swept silver hair. These are original sample assets
awaiting owner direction approval, not acceptance of all future character/environment art.
Glimmer Spark gathers through a lens, travels in a bright arc and breaks into eight warm
shards; a short-effects setting removes its camera cut. Combat rules remain Tidebeat.
Audio, the other spell effects, distant scenery and full animation/creator variety remain
later roadmap work. Expand this visual language only after M1.4's review/device gates.
