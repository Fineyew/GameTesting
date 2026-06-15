from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.router import api_router
from backend.app.core.config import get_settings, validate_runtime_settings
from backend.app.db.session import create_database_provider
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore


def create_app() -> FastAPI:
    settings = get_settings()
    validate_runtime_settings(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.content_catalog = ContentCatalog.build(
            root=settings.content_root,
            manifest_version=int(settings.content_manifest_version),
        )
        database_provider = create_database_provider(settings)
        app.state.database_provider = database_provider
        app.state.vertical_slice_service = VerticalSliceService(
            JsonVerticalSliceStore(settings.vertical_slice_save_path)
        )
        try:
            yield
        finally:
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

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
