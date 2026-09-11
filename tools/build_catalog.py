"""Validate server definitions and generate the deterministic client snapshot."""
import json
import argparse
from pathlib import Path
from backend.app.modules.content.service import ContentCatalog
ROOT = Path(__file__).resolve().parents[1]
def bundle(content_root: Path, output: Path):
    catalog = ContentCatalog.build(content_root)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema": 1, "definitions": [d.model_dump() for d in catalog.list_definitions()]}, sort_keys=True, separators=(",", ":")) + "\n")
    return catalog

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--content-root',type=Path,default=ROOT/'content')
    parser.add_argument('--output',type=Path,default=ROOT/'godot_project/data/catalog.json')
    args = parser.parse_args()
    catalog = bundle(args.content_root,args.output)
    print(f"Validated and bundled {len(catalog.definitions)} definitions")
