# Project continuity

Before changing this project, read README.md, docs/PROJECT_STATE.md and docs/ARCHITECTURE.md;
read docs/GAME_DESIGN.md for gameplay work, then inspect relevant source and recent Git history.
Preserve existing modules, content keys, player IDs, database migrations and working tests.
The repository is the source of truth when conversation recollection differs.

After substantial work, update PROJECT_STATE, ROADMAP, CHANGELOG and relevant canonical docs.
Distinguish implemented/tested/placeholder/planned/blocked. Record actual CI/artifact source SHAs.
Checkpoint stable work remotely during long sessions; never rely on transient build files.
Follow ROADMAP gates: no broad M1 content work before M0 is tested, documented and checkpointed.
Do not claim emulator/desktop checks as physical-phone performance verification.
