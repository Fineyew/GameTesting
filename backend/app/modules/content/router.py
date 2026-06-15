from fastapi import APIRouter, HTTPException

from backend.app.core.config import get_settings
from backend.app.modules.content.schemas import ContentDefinition, ContentManifest
from backend.app.modules.content.service import ContentCatalog

router = APIRouter()


def get_catalog() -> ContentCatalog:
    settings = get_settings()
    return ContentCatalog(
        root=settings.content_root,
        manifest_version=int(settings.content_manifest_version),
    )


@router.get("/manifest", response_model=ContentManifest)
async def manifest() -> ContentManifest:
    return get_catalog().build_manifest()


@router.get("", response_model=list[ContentDefinition])
async def list_content(type: str | None = None) -> list[ContentDefinition]:
    return get_catalog().list_definitions(type)


@router.get("/{content_type}/{key}", response_model=ContentDefinition)
async def get_content(content_type: str, key: str) -> ContentDefinition:
    try:
        return get_catalog().get_definition(content_type, key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
