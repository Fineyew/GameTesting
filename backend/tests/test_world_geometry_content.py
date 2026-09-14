"""Reject unsafe authoring before a catalog can reach either runtime."""
import copy
import json
import shutil
from pathlib import Path

import pytest

from backend.app.modules.content.service import ContentCatalog, ContentValidationError
from backend.app.modules.content.world_geometry import geometry_errors

ROOT = Path(__file__).resolve().parents[2] / "content"


def current_world():
    return json.loads((ROOT / "zones/dawnreef_atoll.json").read_text())["rules"]["world"]


def test_current_geometry_and_legacy_defaults_are_unchanged():
    world = current_world()
    before = copy.deepcopy(world)
    assert geometry_errors(world) == []
    assert world == before
    for key in ("speed", "acceleration", "deceleration", "radius"):
        world.pop(key)
    assert geometry_errors(world) == []


@pytest.mark.parametrize("field,value", [
    ("bounds", None), ("bounds", [-24, -22, 24]),
    ("bounds", [24, -22, -24, 20]), ("bounds", [-24, -22, float("inf"), 20]),
    ("spawn", [0, float("nan")]), ("spawn", [False, 4]),
    ("spawn", [24, 4]), ("spawn", [-9.8, -5]),
    ("blockers", {}), ("blockers", [[0, 0, 0, 1]]),
    ("blockers", [[-25, 0, -20, 1]]), ("blockers", [[0, 0, 1, 1]] * 129),
    ("interactions", []), ("interactions", {"bad": [0, 4, 50]}),
    ("interactions", {"bad": [100, 4]}),
    ("speed", True), ("speed", 0), ("speed", 10**400), ("acceleration", -1),
    ("deceleration", float("nan")), ("radius", .5),
    ("terrain", {"height": 10}),
])
def test_unsafe_or_unimplemented_world_fields_are_rejected(field, value):
    world = current_world()
    world[field] = value
    assert geometry_errors(world)


@pytest.mark.parametrize("world", [None, [], {}, {"bounds": [0, 0, 10, 10]}])
def test_invalid_world_shapes_report_errors_without_crashing(world):
    assert geometry_errors(world)


@pytest.mark.parametrize("world", [None, {**current_world(), "spawn": [12, 5]}])
def test_catalog_refuses_geometry_before_shop_and_story_reference_lookups(tmp_path, world):
    root = tmp_path / "content"
    shutil.copytree(ROOT, root)
    zone = root / "zones/dawnreef_atoll.json"
    payload = json.loads(zone.read_text())
    payload["rules"]["world"] = world
    zone.write_text(json.dumps(payload))
    with pytest.raises(ContentValidationError, match="world"):
        ContentCatalog.build(root)
