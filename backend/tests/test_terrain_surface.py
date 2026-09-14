"""Analytic terrain expectations, not only two implementations agreeing on a bug."""
import copy
import json
import math
from pathlib import Path

import pytest

from backend.app.modules.world.terrain import TerrainSurface

CASES = json.loads((Path(__file__).resolve().parents[2] / "godot_project/tests/terrain_cases.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_analytic_heights_and_non_degenerate_faces(case):
    terrain = TerrainSurface(case["surface"])
    for x, z, expected in case["probes"]:
        assert terrain.sample(x, z)["height"] == pytest.approx(expected)
    for a, b, c in terrain.triangles():
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        assert sum(n*n for n in cross) > 0


@pytest.mark.parametrize("value", [None, [], {}, {"bounds":[0,0,1,1], "cells":{}, "height":3},
    {"bounds":[0,0,0,1], "cells":{}}, {"bounds":[0,0,129,1], "cells":{}},
    {"bounds":[False,0,1,1], "cells":{}}, {"bounds":[.1,0,1,1], "cells":{}},
    {"bounds":[0,0,float("inf"),1], "cells":{}}, {"bounds":[0,0,1,1], "cells":[]},
    *({"bounds":[0,0,1,1], "cells":{key:[0,0,0,0]}} for key in ["00:0","-1:0","1:0","0:1","0:0\n","1e0:0"]),
    *({"bounds":[0,0,1,1], "cells":{"0:0":h}} for h in [[0,0,0], [0,0,0,False], [8001,0,0,0], [0,.5,0,0], [0,float("nan"),0,0], [10**400,0,0,0]])])
def test_reject_malformed_surface(value):
    with pytest.raises(ValueError):
        TerrainSurface(value)


def test_copy_isolation_and_integral_json_numbers():
    definition = {"bounds":[0.,0.,1.,1.],"cells":{"0:0":[1000.,1000,1000,1000]}}
    before = copy.deepcopy(definition)
    terrain = TerrainSurface(definition)
    assert definition == before
    definition["cells"]["0:0"][0] = 8000
    assert terrain.sample(0,0)["height"] == 1
    with pytest.raises(TypeError):
        terrain.cells[(0,0)] = (8,8,8,8)


def test_slope_is_face_gradient_not_increment_size():
    terrain = TerrainSurface({"bounds":[0,0,1,1],"cells":{"0:0":[0,1000,1000,0]}})
    for x in [.0000001,.01,.9,1]:
        assert terrain.sample(x,.5)["slope_degrees"] == pytest.approx(45)


@pytest.mark.parametrize("x,z", [(float("nan"),0),(0,float("inf")),(True,0),(10**400,0),(-.00001,0),(1.00001,0)])
def test_no_query_clamping_or_nonfinite_values(x,z):
    with pytest.raises(ValueError):
        TerrainSurface({"bounds":[0,0,1,1],"cells":{}}).sample(x,z)


def test_max_extent_and_missing_cells():
    terrain = TerrainSurface({"bounds":[-64,-64,64,64],"cells":{}})
    assert terrain.sample(64,64) == {"height":0,"slope_degrees":0,"cell":[127,127],"triangle":0}
    assert len(terrain.triangles()) == 128*128*2
