"""Validate server definitions and generate the deterministic client snapshot."""
import json
from pathlib import Path
from backend.app.modules.content.service import ContentCatalog
ROOT = Path(__file__).resolve().parents[1]
catalog = ContentCatalog.build(ROOT / "content")
path = ROOT / "godot_project/data/catalog.json"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps({"schema": 1, "definitions": [d.model_dump() for d in catalog.list_definitions()]}, sort_keys=True, separators=(",", ":")) + "\n")
print(f"Validated and bundled {len(catalog.definitions)} definitions")
