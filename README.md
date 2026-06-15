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

Create a local PostgreSQL backup from the Compose stack:

```bash
infra/scripts/backup_postgres.sh
```

## Content-first rule

Gameplay content such as spells, quests, NPCs, enemies, items, equipment, shops, loot tables, achievements, crafting recipes, gathering nodes, mounts, dungeons, and zones belongs in `content/` and should be validated before import. Runtime systems should consume content through the content catalog instead of hardcoding gameplay definitions.

Every content file must include `schema_version`, and references between content files must pass `backend/tests/test_content_definitions.py`.
