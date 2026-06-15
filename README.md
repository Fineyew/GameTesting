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

Run the backend locally after installing Python dependencies:

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

Run the self-hosted stack:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## Content-first rule

Gameplay content such as spells, quests, NPCs, enemies, items, shops, loot tables, achievements, crafting recipes, mounts, dungeons, and zones belongs in `content/` and should be validated before import. Runtime systems should consume content through the content catalog instead of hardcoding gameplay definitions.
