# Veilbound Tides - Mobile RPG Architecture Prototype

This repository contains the architecture plan and initial scaffold for an original mobile-first online 3D fantasy RPG built with:

- Godot 4.x client
- FastAPI backend
- PostgreSQL
- Docker Compose
- Nginx
- JWT authentication

The design prioritizes modular systems, low operational cost, self-hosted infrastructure, mobile performance, and data-driven gameplay content.

## Key documents

- [Complete architecture plan](docs/architecture/mobile_first_online_rpg_architecture.md)
- [Brutal 5-year architecture review](docs/architecture/brutal_architecture_review.md)
- [Desktop setup and droplet fresh-start runbook](docs/deployment/desktop_and_droplet_fresh_start_runbook.md)
- [DigitalOcean first deployment checklist](docs/deployment/digitalocean_first_deploy_checklist.md)

## Repository layout

```text
backend/        FastAPI modular-monolith scaffold
content/        Data-driven gameplay definitions
docs/           Architecture and planning documents
godot_project/  Godot 4.x client scaffold
infra/          Docker Compose and Nginx deployment files
```

## Local validation

Run the content validation tests:

```bash
python -m unittest discover backend/tests
```

Use `python3` if your environment does not provide a `python` alias:

```bash
python3 -m unittest discover backend/tests
```

Run the backend locally after installing Python dependencies:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Run database migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

Run the self-hosted stack:

```bash
docker compose -f infra/docker-compose.yml up --build
```

Copy `infra/.env.example` to `infra/.env` and replace all secrets before running a shared or production-like environment.

For HTTPS deployment, place TLS files at:

```text
infra/certs/fullchain.pem
infra/certs/privkey.pem
```

The default Nginx deployment redirects HTTP to HTTPS and will not start without mounted certificates.

Create a local PostgreSQL backup from the Compose stack:

```bash
infra/scripts/backup_postgres.sh
```

## Content-first rule

Gameplay content such as spells, quests, NPCs, enemies, items, equipment, shops, loot tables, achievements, crafting recipes, gathering nodes, mounts, dungeons, and zones belongs in `content/` and should be validated before import. Runtime systems should consume content through the content catalog instead of hardcoding gameplay definitions.

Every content file must include `schema_version`, and references between content files must pass `backend/tests/test_content_definitions.py`.

## Playable vertical slice

The current playable loop is intentionally small:

1. `POST /api/v1/auth/register`
2. `POST /api/v1/characters`
3. `GET /api/v1/world/characters/{character_id}`
4. `POST /api/v1/world/characters/{character_id}/quests/lantern_well_first_light/accept`
5. `POST /api/v1/world/characters/{character_id}/combat/fight`
6. `POST /api/v1/world/characters/{character_id}/save`
7. `POST /api/v1/auth/logout`
8. `POST /api/v1/auth/login`
9. `GET /api/v1/world/characters/{character_id}`

This loop supports one account, one playable character, one starting zone, one NPC, one quest, one enemy, three starter spells, XP gain, leveling, inventory rewards, save/load, logout, and persisted login.

Local vertical-slice save data is written to `var/vertical_slice_save.json` by default and is ignored by Git. Docker deployments mount `/app/var` to the `vertical_slice_saves` named volume so the JSON save survives backend container recreation.

## Godot vertical-slice client

Open `godot_project/project.godot` in Godot 4.x and press Play. The current main scene is a simple debug UI for the deployed backend at:

```text
https://game.surveyroute.work/api/v1
```

The screen can register/login, create a character, enter the world, accept the starter quest, fight the starter enemy, save, logout, and display the returned character state.
