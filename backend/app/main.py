from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
import time
from collections import deque

from backend.app.api.router import api_router
from backend.app.core.config import get_settings, validate_runtime_settings
from backend.app.db.session import create_database_provider
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
from backend.app.modules.vertical_slice.encounters import EncounterService
from backend.app.modules.combat.engine import CombatEngine
from backend.app.modules.quests.rules import QuestRules
from backend.app.modules.vertical_slice.story import StoryService
from backend.app.modules.world.hub import WorldHub
from backend.app.modules.world.router import router as world_router
from backend.app.db.player_store import PostgresPlayerStore


def create_app() -> FastAPI:
    settings = get_settings()
    validate_runtime_settings(settings)
    if settings.player_store not in {"json", "postgres"}:
        raise ValueError("VT_PLAYER_STORE must be json or postgres")
    if settings.environment.lower() in {"production", "staging"} and settings.player_store != "postgres":
        raise ValueError("staging and production require PostgreSQL persistence")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.content_catalog = ContentCatalog.build(
            root=settings.content_root,
            manifest_version=int(settings.content_manifest_version),
        )
        database_provider = create_database_provider(settings)
        app.state.database_provider = database_provider
        store = PostgresPlayerStore(settings.database_url) if settings.player_store == "postgres" else JsonVerticalSliceStore(settings.vertical_slice_save_path)
        quest_rules = QuestRules(app.state.content_catalog)
        players = VerticalSliceService(store, quest_rules)
        app.state.vertical_slice_service = players
        app.state.story = StoryService(players, quest_rules)
        app.state.encounters = EncounterService(players, CombatEngine(app.state.content_catalog), app.state.content_catalog)
        geometry = app.state.content_catalog.get_definition("zones", "dawnreef_atoll").rules["world"]
        app.state.world_hub = WorldHub(geometry, players)
        app.state.world_hub.start()
        try:
            yield
        finally:
            await app.state.world_hub.stop()
            if isinstance(store, PostgresPlayerStore):
                store.engine.dispose()
            await database_provider.dispose()

    app = FastAPI(
        title=settings.project_name,
        version=settings.api_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.project_name}

    attempts = {}

    @app.middleware("http")
    async def limit_auth(request: Request, call_next):
        if request.url.path in {"/api/v1/auth/login", "/api/v1/auth/register"}:
            ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            bucket = attempts.setdefault(ip, deque())
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= 20:
                return JSONResponse({"detail": "Too many attempts; wait one minute."}, status_code=429)
            bucket.append(now)
            if len(attempts) > 4096:
                del attempts[next(iter(attempts))]
        return await call_next(request)

    @app.exception_handler(IntegrityError)
    async def duplicate_identity(request: Request, exc: IntegrityError):
        return JSONResponse({"detail": "That account or character name is already in use."}, status_code=409)

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(world_router, prefix="/api/v1")
    return app


app = create_app()
