import hashlib
import json
from pathlib import Path

from backend.app.modules.content.schemas import (
    ContentDefinition,
    ContentManifest,
    ContentManifestEntry,
)


class ContentCatalog:
    """File-backed catalog used by the scaffold before database publishing exists."""

    def __init__(self, root: Path, manifest_version: int = 1) -> None:
        self.root = root
        self.manifest_version = manifest_version

    def list_definitions(self, content_type: str | None = None) -> list[ContentDefinition]:
        definitions = [self._load_definition(path) for path in self._definition_paths()]
        if content_type is not None:
            definitions = [item for item in definitions if item.type == content_type]
        return sorted(definitions, key=lambda item: (item.type, item.key, item.version))

    def get_definition(self, content_type: str, key: str) -> ContentDefinition:
        for definition in self.list_definitions(content_type):
            if definition.key == key:
                return definition
        raise KeyError(f"Content definition not found: {content_type}/{key}")

    def build_manifest(self) -> ContentManifest:
        entries: list[ContentManifestEntry] = []
        for path in self._definition_paths():
            definition = self._load_definition(path)
            entries.append(
                ContentManifestEntry(
                    type=definition.type,
                    key=definition.key,
                    version=definition.version,
                    checksum=self._checksum(path),
                    path=str(path.relative_to(self.root)),
                )
            )
        return ContentManifest(
            manifest_version=self.manifest_version,
            entries=sorted(entries, key=lambda item: (item.type, item.key)),
        )

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
