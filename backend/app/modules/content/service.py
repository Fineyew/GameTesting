import hashlib
import json
from pathlib import Path

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


class ContentCatalog:
    """Validated file-backed catalog used before database publishing exists."""

    def __init__(self, root: Path, manifest_version: int = 1) -> None:
        self.root = root
        self.manifest_version = manifest_version
        self._definitions: dict[tuple[str, str], ContentDefinition] | None = None
        self._checksums: dict[tuple[str, str], str] | None = None
        self._paths: dict[tuple[str, str], Path] | None = None

    def list_definitions(self, content_type: str | None = None) -> list[ContentDefinition]:
        self._ensure_loaded()
        assert self._definitions is not None
        definitions = list(self._definitions.values())
        if content_type is not None:
            definitions = [item for item in definitions if item.type == content_type]
        return sorted(definitions, key=lambda item: (item.type, item.key, item.version))

    def get_definition(self, content_type: str, key: str) -> ContentDefinition:
        self._ensure_loaded()
        assert self._definitions is not None
        try:
            return self._definitions[(content_type, key)]
        except KeyError as exc:
            raise ContentNotFoundError(f"Content definition not found: {content_type}/{key}") from exc

    def build_manifest(self) -> ContentManifest:
        self._ensure_loaded()
        assert self._definitions is not None
        assert self._checksums is not None
        assert self._paths is not None

        entries: list[ContentManifestEntry] = []
        for identity, definition in self._definitions.items():
            path = self._paths[identity]
            entries.append(
                ContentManifestEntry(
                    type=definition.type,
                    key=definition.key,
                    version=definition.version,
                    checksum=self._checksums[identity],
                    path=str(path.relative_to(self.root)),
                )
            )
        return ContentManifest(
            manifest_version=self.manifest_version,
            entries=sorted(entries, key=lambda item: (item.type, item.key)),
        )

    def _ensure_loaded(self) -> None:
        if self._definitions is not None:
            return

        report = validate_content_tree(self.root)
        if not report.is_valid:
            raise ContentValidationError("; ".join(report.errors))

        definitions: dict[tuple[str, str], ContentDefinition] = {}
        checksums: dict[tuple[str, str], str] = {}
        paths: dict[tuple[str, str], Path] = {}

        for identity, loaded in report.definitions.items():
            definition = self._load_definition(loaded.path)
            definitions[identity] = definition
            checksums[identity] = self._checksum(loaded.path)
            paths[identity] = loaded.path

        self._definitions = definitions
        self._checksums = checksums
        self._paths = paths

    def _definition_paths(self) -> list[Path]:
        if not self.root.exists():
            return []
        return sorted(path for path in self.root.rglob("*.json") if path.is_file())

    def _load_definition(self, path: Path) -> ContentDefinition:
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
