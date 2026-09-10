# Veilbound Tides — roadmap

Updated 2026-09-10. Distinguish engineering gates from unverified physical-device/release gates.

## M0 — foundation handoff (engineering complete)

- [x] Restore and remotely checkpoint modular client, combat, presence and PostgreSQL adapter.
- [x] Validate real PostgreSQL migrations, persistence and concurrent/retried actions in CI.
- [x] Validate actual Godot client against API and a second connected player.
- [x] Import/movement/UI smoke; static material batching and initial lighting adjustment.
- [x] Reconcile PROJECT_STATE and CHANGELOG with completed CI evidence.
- [x] Fix the observed coastline/floor overlap and inspect fresh renders.
- [x] Automate, retain and signature-check an ARM64 APK; verify Android runtime install/start.
- [x] Verify visible world and touch locomotion after resume (run 34430377236 at 69457a4).
- [x] Record physical Android testing status, performance targets, remaining risks and build provenance.
- [x] Complete canonical documentation and checkpoint M0 source/artifacts remotely.

M0 engineering completion requires a reproducible retained APK, automated checks and
honest device-status documentation. Physical phone thermal/touch/network validation is
an open release gate; never call an emulator or desktop result a physical-phone pass.
No broad M1 content production before this engineering checkpoint.

## M1 — authored vertical slice (M1.2 in validation)

- [x] M1.1: catalog-owned NPC dialogue/branches/conditions with server-owned cursors.
- [x] Validated quest offers, ordered defeat/inspect/talk objectives and once-only rewards.
- [x] One Mara follow-up through existing reeds/cistern landmarks; data-driven HUD/journal.
- [x] Preserve old saves/starter IDs; prove API authority, retries, concurrent turn-ins and
  PostgreSQL persistence; real Godot story integration and Android runtime gates pass.

M1.1 code/APK source 4efd3a6 passed all jobs in run 34431891977 (38 tests). M0 remains
checkpointed at 1044f95. No bulk content was produced; the cistern dungeon is still sealed.

**M1.2 — implemented; final CI/artifact handoff pending**

- [x] Three short Mara lessons make Beacon Trace, Reed Aegis and Seam Lance obtainable.
- [x] Six-slot persistent folio, ownership/catalog/duplicate checks, stale-write/retry guards.
- [x] Prepared-only combat with universal Brace/Gather; active-combat preparation lock.
- [x] Touch Folio panel, costs/effects/source hints, learned/prepared distinction and safe retry UI.
- [x] JSON old-save/retry/authority coverage and Godot folio smoke checks.
- [x] Complete extended Godot/API acquisition, folio and earned-spell combat integration.
- [ ] Complete PostgreSQL, render and Android runtime gates.
- [ ] Retain verified ARM64 0.2.2/code 4, reconcile handoff and checkpoint M1.2.

**Recommended next: M1.3 (not started)** — one equipment/vendor loop using the existing
Dawnreef supply cart/item definitions: server-owned buy/equip, useful item comparison,
atomic currency/inventory updates and retry/concurrency tests. Preserve the six-spell
combat foundation. Do not start bulk quests/spells/worlds, a dungeon or a new discipline.
Stop after the M1.2 checkpoint until the next authorized working session.

Target: one town plus adventure region, 18 varied quests, 18 working obtainable spells,
five enemies, eight recurring NPCs, one dungeon with a phased boss, equipment/vendor,
two resources/recipes, an earned mount and safe social play. Housing proof of concept
follows core stability. Physical Android performance, account lifecycle, moderation,
backup/restore and old-save migration are release gates.

## Later

Parties, friends, guilds, trading, housing, pets, minigames, crafting expansion,
world events and more regions. Android first; Windows then iOS. No monetization yet.
