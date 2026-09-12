from fastapi import APIRouter, Request

from backend.app.core.config import get_settings
from backend.app.modules.characters.router import router as characters_router
from backend.app.modules.combat.router import router as combat_router
from backend.app.modules.content.router import router as content_router
from backend.app.modules.inventory.router import router as inventory_router
from backend.app.modules.quests.router import router as quests_router
from backend.app.modules.registry import module_registry
from backend.app.modules.social.router import router as social_router
from backend.app.modules.vertical_slice.router import router as vertical_slice_router

api_router = APIRouter()


@api_router.get("/server-info", tags=["server"])
async def server_info(request: Request) -> dict[str, str | int]:
    settings = get_settings()
    return {
        "api_version": settings.api_version,
        "world_protocol": 2,
        "geometry_digest": request.app.state.world_hub.digest,
        "geometry_revision": request.app.state.world_hub.revision,
        "story_protocol": 1,
        "folio_protocol": 1,
        "commerce_protocol": 1,
        "item_use_protocol": 1,
        "minimum_client_version": settings.minimum_client_version,
        "content_manifest_version": settings.content_manifest_version,
    }


@api_router.get("/modules", tags=["server"])
async def modules() -> list[dict[str, object]]:
    return module_registry()


api_router.include_router(content_router, prefix="/content", tags=["content"])
api_router.include_router(vertical_slice_router)
api_router.include_router(characters_router, prefix="/characters", tags=["characters"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
api_router.include_router(quests_router, prefix="/quests", tags=["quests"])
api_router.include_router(combat_router, prefix="/combat", tags=["combat"])
api_router.include_router(social_router, prefix="/social", tags=["social"])
