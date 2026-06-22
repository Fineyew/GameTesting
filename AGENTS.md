# Veilbound Tides

See `README.md` for the project overview and the canonical command list (tests, backend run, migrations, Docker Compose).

## Cursor Cloud specific instructions

### Services / layout
- `backend/` — FastAPI modular monolith. This is the only service runnable in the cloud dev environment.
- The playable **vertical slice** (`backend/app/modules/vertical_slice/`) persists to a **local JSON file**, not Postgres. The full register → create character → quest → fight → save → logout → login loop runs with **no database**. Save file defaults to `var/vertical_slice_save.json` (gitignored).
- `godot_project/` — Godot 4.x client; requires the Godot editor and points at a remote deployed backend, so it is not run headlessly here.
- Postgres + Alembic (`backend/db/models.py`, `backend/alembic/`) back the persistent ORM models only; they are not needed for the vertical slice. `docker compose -f infra/docker-compose.yml up` additionally requires `infra/.env` with `POSTGRES_PASSWORD` and `VT_JWT_SECRET` set.

### Python env
- The update script provisions a virtualenv at `.venv/` and installs `backend/requirements.txt` plus dev tools `ruff`, `pytest`, `httpx`. Use `.venv/bin/python`, `.venv/bin/ruff`, `.venv/bin/pytest`.
- Requires Python ≥ 3.11; the VM ships 3.12.

### Run / lint / test
- Run dev server: `VT_DEBUG=true VT_ENVIRONMENT=local .venv/bin/uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`. `VT_DEBUG=true` is required to expose `/docs` and `/redoc` (they are disabled otherwise).
- Default scaffold `jwt_secret` (`change-me-in-production`) and `database_url` are fine for `local`/`test`; `validate_runtime_settings` only enforces non-placeholder secrets for `staging`/`production`.
- Lint: `.venv/bin/ruff check backend` — currently reports 2 pre-existing `F402` warnings in `backend/app/modules/content/validation.py` (not introduced by setup).
- Tests: `.venv/bin/pytest -q` (or `python -m unittest discover backend/tests`).
