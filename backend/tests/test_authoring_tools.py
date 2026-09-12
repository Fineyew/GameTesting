"""Authoring failures, deterministic bundles and isolated examples using production rules."""
import hashlib
import json
from pathlib import Path
import shutil
import pytest
from tools.author_content import ROOT, DEMO, create_example, diagnostics, encounter_preview
from tools.build_catalog import bundle


def digest(root):
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*/*.json')}


def test_current_catalog_round_trips_without_mutation(tmp_path):
    before=digest(ROOT/'content')
    output=tmp_path/'catalog.json';bundle(ROOT/'content',output)
    assert output.read_bytes()==(ROOT/'godot_project/data/catalog.json').read_bytes()
    assert diagnostics(ROOT/'content')['errors']==[]
    assert len(diagnostics(ROOT/'content')['warnings'])==26
    assert digest(ROOT/'content')==before
    malformed=tmp_path/'bad-bindings.json'
    for value in ([],{'schema':1,'asset_references':[],'interactions':{}}):
        malformed.write_text(json.dumps(value))
        assert diagnostics(ROOT/'content',bindings_path=malformed)['errors']


def test_example_is_repeatable_isolated_and_preserves_old_ids(tmp_path):
    before=digest(ROOT/'content')
    a=create_example(tmp_path/'a');b=create_example(tmp_path/'b')
    assert digest(a)==digest(b)
    assert digest(ROOT/'content')==before
    changed={key for key,value in before.items() if digest(a)[key]!=value}
    assert changed=={'npcs/mara_lanternwright.json','dialogue/mara_first_meeting.json'}
    assert len(digest(a))==len(before)+1
    assert (a/f'quests/{DEMO}.json').exists()
    assert not diagnostics(a)['errors']
    with pytest.raises(ValueError,match='already exists'):create_example(tmp_path/'a')
    with pytest.raises(ValueError,match='separate'):create_example(ROOT/'content/not-an-output')


@pytest.fixture
def workspace(tmp_path):
    source=tmp_path/'content';shutil.copytree(ROOT/'content',source)
    bindings=tmp_path/'bindings.json';shutil.copy2(ROOT/'authoring/bindings.json',bindings)
    return source,bindings


def modify(path,edit):
    value=json.loads(path.read_text());edit(value);path.write_text(json.dumps(value))


def test_unreachable_dialogue_branch_rejected(workspace):
    source,bindings=workspace
    modify(source/'dialogue/mara_first_meeting.json',lambda v:v['rules']['nodes'].update(orphan={'text':'Unreachable','options':[]}))
    assert any('unreachable branch' in x for x in diagnostics(source,bindings_path=bindings)['errors'])


def test_schema_known_but_unimplemented_quest_objective_rejected(workspace):
    source,bindings=workspace
    modify(source/'quests/an_answer_in_the_reeds.json',lambda v:v['rules']['objectives'].__setitem__(0,{'key':'unimplemented','type':'collect_item','item_key':'clean_reed_cloth','quantity':1}))
    assert any('no runtime handler' in x for x in diagnostics(source,bindings_path=bindings)['errors'])


@pytest.mark.parametrize('change,reason',[
    (lambda d:d['interactions'].pop('mara_lanternwright'),'missing interaction binding'),
    (lambda d:d['interactions']['mara_lanternwright'].update(handler='fish'),'unsupported interaction handler'),
    (lambda d:d['interactions']['mara_lanternwright'].update(scene='res://absent.tscn'),'missing scene binding'),
    (lambda d:d['interactions']['mara_lanternwright'].update(handler_source='README.md'),'no declared runtime dispatch'),
    (lambda d:d['asset_references'].pop(next(iter(d['asset_references']))),'missing production status'),
    (lambda d:d['asset_references'][next(iter(d['asset_references']))].update(status='final'),'final asset is missing'),
    (lambda d:d['interactions']['mara_lanternwright'].update(binding_source='../escape'),'escapes project root'),
])
def test_forged_or_dangling_bindings_rejected(workspace,change,reason):
    source,bindings=workspace;modify(bindings,change)
    assert any(reason in x for x in diagnostics(source,bindings_path=bindings)['errors'])


def test_existing_file_is_not_automatically_final(workspace):
    source,bindings=workspace
    path='res://icon.svg'
    modify(source/'npcs/mara_lanternwright.json',lambda v:v['assets'].update(authoring_test=path))
    modify(bindings,lambda v:v['asset_references'].update({path:{'status':'final','editable_source':'godot_project/icon.svg','license':'Original project source'}}))
    assert any('acceptance record' in x for x in diagnostics(source,bindings_path=bindings)['errors'])


def test_encounter_preview_uses_real_engine_without_save_side_effects():
    before=digest(ROOT/'content')
    first=encounter_preview(ROOT/'content','fog_thorn_lurker',['gather','glimmer_spark'],['glimmer_spark'])
    assert first==encounter_preview(ROOT/'content','fog_thorn_lurker',['gather','glimmer_spark'],['glimmer_spark'])
    assert first['frames'][-1]['enemy_vigor']<first['frames'][0]['enemy_vigor']
    with pytest.raises(ValueError):encounter_preview(ROOT/'content','fog_thorn_lurker',['seam_lance'],['glimmer_spark'])
    assert digest(ROOT/'content')==before
