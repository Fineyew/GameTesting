from typing import Any

from pydantic import BaseModel, Field


class ContentDisplay(BaseModel):
    name: str
    summary: str | None = None
    description: str | None = None


class ContentDefinition(BaseModel):
    type: str = Field(min_length=1)
    key: str = Field(min_length=1)
    schema_version: int = Field(ge=1)
    version: int = Field(ge=1)
    display: ContentDisplay
    tags: list[str] = Field(default_factory=list)
    assets: dict[str, Any] = Field(default_factory=dict)
    rules: dict[str, Any] = Field(default_factory=dict)
    localization: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContentManifestEntry(BaseModel):
    type: str
    key: str
    version: int
    checksum: str
    path: str


class ContentManifest(BaseModel):
    manifest_version: int
    entries: list[ContentManifestEntry]
