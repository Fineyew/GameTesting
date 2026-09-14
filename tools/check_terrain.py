"""Compare independent Python/Godot surfaces and actual Godot physics ray hits."""
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile

from backend.app.modules.world.terrain import TerrainSurface
from backend.app.modules.world.traversal import move
from backend.app.modules.world.protocol import geometry_digest

ROOT = Path(__file__).resolve().parents[1]


def check():
    cases = json.loads((ROOT / "godot_project/tests/terrain_cases.json").read_text())
    randomizer = random.Random(1707)
    for index in range(24):
        cells = {f"{x}:{z}":[randomizer.randint(-8000,8000) for _ in range(4)]
                 for x in range(3) for z in range(3) if randomizer.random() > .25}
        cases.append({"name":f"seeded_{index}", "surface":{"bounds":[-2,-2,1,1],"cells":cells},
                      "probes":[],"rays":[]})
    live = json.loads((ROOT/'content/zones/dawnreef_atoll.json').read_text())["rules"]["world"]
    cases.append({"name":"live_route","surface":live["terrain"],"probes":[],"rays":[[6,14.5]],"blockers":live["blockers"]})
    for case in cases:
        terrain = TerrainSurface(case["surface"])
        b = terrain.bounds
        queries = [[p[0],p[1]] for p in case["probes"]]
        queries += [[randomizer.uniform(b[0],b[2]),randomizer.uniform(b[1],b[3])] for _ in range(64)]
        case["expected_samples"] = [{"at":q,"result":terrain.sample(*q)} for q in queries]
        case["expected_triangles"] = terrain.triangles()
        motions=[]
        for _ in range(20):
            start=[randomizer.uniform(b[0]+.36,b[2]-.36),randomizer.uniform(b[1]+.36,b[3]-.36)]
            delta=[randomizer.uniform(-.5,.5),randomizer.uniform(-.5,.5)]
            result,stopped=move(terrain,start,delta,case.get("blockers",[]))
            motions.append({"start":start,"delta":delta,"position":result,"stopped":stopped})
        if case["name"]=="live_route":
            pos=[6,9]
            for _ in range(100):
                delta=[0,.1]
                result,stopped=move(terrain,pos,delta,case["blockers"])
                motions.append({"start":pos,"delta":delta,"position":result,"stopped":stopped})
                pos=result
        case["motions"]=motions
        # Interior random rays avoid ambiguous exact shared-edge ownership in physics.
        case["rays"] += queries[-8:]
        case["expected_ray_heights"] = [terrain.sample(*q)["height"] for q in case["rays"]]
    invalid = [None, {}, {"bounds":[0,0,1,1],"cells":{},"extra":1}]
    for bounds in [[0,0,0,1], [0,0,129,1], [False,0,1,1], [.25,0,1,1]]:
        invalid.append({"bounds":bounds,"cells":{}})
    for key in ["00:0","-1:0","1:0","0:1","0:0\n","1e0:0"]:
        invalid.append({"bounds":[0,0,1,1],"cells":{key:[0,0,0,0]}})
    for heights in [[0,0,0], [True,0,0,0], [8001,0,0,0], [.5,0,0,0]]:
        invalid.append({"bounds":[0,0,1,1],"cells":{"0:0":heights}})
    for definition in invalid:
        try:
            TerrainSurface(definition)
        except ValueError:
            continue
        raise AssertionError("Python accepted invalid fixture")
    with tempfile.TemporaryDirectory(prefix="vt-terrain-") as temporary:
        path = Path(temporary)/"terrain.json"
        path.write_text(json.dumps({"cases":cases,"invalid":invalid,"geometry":live,"digest":geometry_digest(live)}))
        try:
            result = subprocess.run([os.environ.get("GODOT_BIN","godot"),"--headless","--path",
                                     str(ROOT/"godot_project"),"--script","res://tests/terrain.gd","--",str(path)],
                                    capture_output=True,text=True,timeout=30)
        except subprocess.TimeoutExpired as error:
            print(error.stdout, error.stderr)
            raise SystemExit("Terrain check timed out; see captured engine diagnostics") from error
        output = result.stdout+result.stderr
        print(output)
        if result.returncode or "ERROR:" in output or "SCRIPT ERROR" in output or "TERRAIN_PARITY_PASS" not in output:
            raise SystemExit(1)


if __name__ == "__main__":
    check()
