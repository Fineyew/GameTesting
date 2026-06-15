import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from backend.app.modules.content.schemas import (
    ContentDefinition,
    ContentManifest,
    ContentManifestEntry,
)
from backend.app.modules.content.validation import validate_content_tree


class ContentCatalogError(RuntimeError):
    pass


class ContentNotFoundError(ContentCatalogError):
    pass


class ContentValidationError(ContentCatalogError):
    pass


@dataclass(frozen=True)
class ContentCatalog:
    """Immutable validated content snapshot used before database publishing exists."""

    root: Path
    manifest_version: int
    definitions: Mapping[tuple[str, str], ContentDefinition]
    checksums: Mapping[tuple[str, str], str]
    paths: Mapping[tuple[str, str], Path]

    @classmethod
    def build(cls, root: Path, manifest_version: int = 1) -> "ContentCatalog":
        report = validate_content_tree(root)
        if not report.is_valid:
            raise ContentValidationError("; ".join(report.errors))

        definitions: dict[tuple[str, str], ContentDefinition] = {}
        checksums: dict[tuple[str, str], str] = {}
        paths: dict[tuple[str, str], Path] = {}

        for identity, loaded in report.definitions.items():
            definition = cls._load_definition(loaded.path)
            definitions[identity] = definition
            checksums[identity] = cls._checksum(loaded.path)
            paths[identity] = loaded.path

        return cls(
            root=root,
            manifest_version=manifest_version,
            definitions=MappingProxyType(definitions),
            checksums=MappingProxyType(checksums),
            paths=MappingProxyType(paths),
        )

    def list_definitions(self, content_type: str | None = None) -> list[ContentDefinition]:
        definitions = list(self.definitions.values())
        if content_type is not None:
            definitions = [item for item in definitions if item.type == content_type]
        return sorted(definitions, key=lambda item: (item.type, item.key, item.version))

    def get_definition(self, content_type: str, key: str) -> ContentDefinition:
        try:
            return self.definitions[(content_type, key)]
        except KeyError as exc:
            raise ContentNotFoundError(f"Content definition not found: {content_type}/{key}") from exc

    def build_manifest(self) -> ContentManifest:
        entries: list[ContentManifestEntry] = []
        for identity, definition in self.definitions.items():
            path = self.paths[identity]
            entries.append(
                ContentManifestEntry(
                    type=definition.type,
                    key=definition.key,
                    version=definition.version,
                    checksum=self.checksums[identity],
                    path=str(path.relative_to(self.root)),
                )
            )
        return ContentManifest(
            manifest_version=self.manifest_version,
            entries=sorted(entries, key=lambda item: (item.type, item.key)),
        )

    @staticmethod
    def _load_definition(path: Path) -> ContentDefinition:
        payload = json.loads(path.read_text(encoding="utf-8"))
        definition = ContentDefinition.model_validate(payload)
        expected_type = path.parent.name
        if definition.type != expected_type:
            raise ValueError(
                f"{path} declares type '{definition.type}' but is stored under '{expected_type}'"
            )
        if definition.key != path.stem:
            raise ValueError(f"{path} declares key '{definition.key}' but filename is '{path.stem}'")
        return definition

    @staticmethod
    def _checksum(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()
