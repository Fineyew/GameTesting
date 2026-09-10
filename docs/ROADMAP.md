# Veilbound Tides — roadmap

Updated 2026-09-10. Distinguish engineering gates from unverified physical-device/release gates.

## M0 — foundation handoff (current)

- [x] Restore and remotely checkpoint modular client, combat, presence and PostgreSQL adapter.
- [x] Validate real PostgreSQL migrations, persistence and concurrent/retried actions in CI.
- [x] Validate actual Godot client against API and a second connected player.
- [x] Import/movement/UI smoke; static material batching and initial lighting adjustment.
- [x] Reconcile PROJECT_STATE and CHANGELOG with completed CI evidence.
- [ ] Fix the observed coastline/floor overlap and inspect fresh renders.
- [ ] Automate, retain and signature-check an ARM64 APK; verify Android runtime install/start.
- [ ] Record physical Android testing status, performance targets, remaining risks and build provenance.
- [ ] Complete canonical documentation and checkpoint M0 source/artifacts remotely.

M0 engineering completion requires a reproducible retained APK, automated checks and
honest device-status documentation. Physical phone thermal/touch/network validation is
an open release gate; never call an emulator or desktop result a physical-phone pass.
No broad M1 content production before this engineering checkpoint.

## M1 — authored vertical slice (planned)

Start with a narrow content-framework increment: generic server-owned quest/dialogue
execution, validated objectives/rewards and a small authored continuation of Mara's
story. Reuse the existing catalog and aggregate transactions. Then make the remaining
initial spells obtainable and add folio selection; expand content only after this works.

Target: one town plus adventure region, 18 varied quests, 18 working obtainable spells,
five enemies, eight recurring NPCs, one dungeon with a phased boss, equipment/vendor,
two resources/recipes, an earned mount and safe social play. Housing proof of concept
follows core stability. Physical Android performance, account lifecycle, moderation,
backup/restore and old-save migration are release gates.

## Later

Parties, friends, guilds, trading, housing, pets, minigames, crafting expansion,
world events and more regions. Android first; Windows then iOS. No monetization yet.
