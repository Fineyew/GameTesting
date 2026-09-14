"""Generate isolated before/after effect review data with the actual combat engine."""
import argparse
import json
from pathlib import Path
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.combat.engine import CombatEngine

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT/'godot_project/tests/fixtures/tidebeat.json'

def build():
    catalog = ContentCatalog.build(ROOT/'content')
    spells = ['glimmer_spark','beacon_trace','root_snare','reed_aegis','tide_mend','seam_lance']
    engine = CombatEngine(catalog)
    frames = {}
    for key in spells+['brace','gather','prism_needle','reed_stitch','stillwater_knot']:
        prepared = spells if key in spells+['brace','gather'] else [key,*spells[:5]]
        enemy = 'shellfold_sifter' if key in ['prism_needle','reed_stitch'] else ('hushfin_ray' if key=='stillwater_knot' else 'fog_thorn_lurker')
        before = engine.begin(enemy,24,prepared)
        before.update(id='presentation-fixture-'+key,focus=6,mark=6)
        frames[key] = {'before':before,'after':engine.resolve(before,key)}
    return {'mode':'isolated engine review; no account, rewards or persistence','frames':frames}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    text = json.dumps(build(),sort_keys=True,separators=(',',':'))+'\n'
    if args.check:
        assert PATH.read_text()==text,'Regenerate spell review fixtures after changing the catalog or combat rules'
    else:
        PATH.parent.mkdir(parents=True,exist_ok=True)
        PATH.write_text(text)
    print('SPELL_REVIEW_FIXTURES_PASS: eleven outcomes from the real engine, six prepared slots each, no player store')
