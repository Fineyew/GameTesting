from fastapi import APIRouter, Depends, HTTPException, Request

from backend.app.modules.content.schemas import ContentDefinition, ContentManifest
from backend.app.modules.content.service import (
    ContentCatalog,
    ContentNotFoundError,
)

router = APIRouter()


def get_catalog(request: Request) -> ContentCatalog:
    return request.app.state.content_catalog


@router.get("/manifest", response_model=ContentManifest)
async def manifest(catalog: ContentCatalog = Depends(get_catalog)) -> ContentManifest:
    return catalog.build_manifest()


@router.get("", response_model=list[ContentDefinition])
async def list_content(
    type: str | None = None,
    catalog: ContentCatalog = Depends(get_catalog),
) -> list[ContentDefinition]:
    return catalog.list_definitions(type)


@router.get("/{content_type}/{key}", response_model=ContentDefinition)
async def get_content(
    content_type: str,
    key: str,
    catalog: ContentCatalog = Depends(get_catalog),
) -> ContentDefinition:
    try:
        return catalog.get_definition(content_type, key)
    except ContentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
