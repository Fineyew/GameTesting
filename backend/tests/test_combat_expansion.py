"""New tactical choices, catalog progression and earned lessons retain aggregate authority."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import pytest

from backend.app.modules.characters.progression import CharacterProgression
from backend.app.modules.combat.engine import CombatEngine
from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.content.validation import validate_content_tree
from backend.app.modules.quests.rules import QuestRules
from backend.app.modules.vertical_slice.domain import CharacterRecord
from backend.app.modules.vertical_slice.encounters import EncounterService
from backend.app.modules.vertical_slice.folio import FolioService
from backend.app.modules.vertical_slice.service import VerticalSliceService
from backend.app.modules.vertical_slice.store import JsonVerticalSliceStore
from backend.app.modules.vertical_slice.story import StoryService

ROOT = Path(__file__).resolve().parents[2]
BASE = ['glimmer_spark','root_snare','tide_mend','beacon_trace','reed_aegis','seam_lance']
LESSONS = ['light_between_plates','a_kindly_weave','keep_the_quiet']

@pytest.fixture
def catalog():
    return ContentCatalog.build(ROOT/'content')

@pytest.mark.parametrize('xp,level',[(0,1),(99,1),(100,2),(199,2),(200,3),(500,6),(1100,12)])
def test_cumulative_threshold_boundaries(catalog,xp,level):
    progression = CharacterProgression(catalog)
    assert progression.level_for(xp)==level
    assert progression.threshold_for(level)<=xp<progression.threshold_for(level+1)

def test_old_levels_are_not_removed_and_catalog_controls_thresholds(catalog):
    replacement = ContentCatalog.build(ROOT/'content')
    replacement.get_definition('progression','wayfarer').rules.update(level_thresholds=[0,80,150],continued_level_step=90)
    progression = CharacterProgression(replacement)
    assert [progression.level_for(x) for x in [79,80,149,150,239,240]]==[1,2,2,3,3,4]
    record = CharacterRecord.create('account','Preserved','lumenfolk','dawnreef_local')
    record.level=8
    record.experience=150
    before=record.public_state()
    progression.settle(record)
    assert record.public_state()==before
    for invalid in [-1,True,1.5]:
        with pytest.raises(ValueError): progression.level_for(invalid)

def test_armor_openings_and_piercing_preserve_old_spell_numbers(catalog):
    engine=CombatEngine(catalog)
    closed=engine.begin('shellfold_sifter',30,['glimmer_spark','prism_needle'])
    before=deepcopy(closed)
    normal=engine.resolve(closed,'glimmer_spark')
    pierced=engine.resolve(closed,'prism_needle')
    assert closed==before
    assert normal['enemy_vigor']==34 and pierced['enemy_vigor']==27
    assert normal['intent']['guard']==0
    assert engine.resolve(normal,'glimmer_spark')['enemy_vigor']==26
    closed['mark']=6
    marked=engine.resolve(closed,'glimmer_spark')
    assert marked['enemy_vigor']==28 and marked['mark']==0
    old=engine.begin('fog_thorn_lurker',30,['glimmer_spark'])
    assert engine.resolve(old,'glimmer_spark')['enemy_vigor']==24

def test_focus_drain_order_ward_expiry_caps_and_combined_heal_guard(catalog):
    engine=CombatEngine(catalog)
    ray=engine.begin('hushfin_ray',30,['glimmer_spark','stillwater_knot'])
    unprotected=engine.resolve(ray,'glimmer_spark')
    protected=engine.resolve(ray,'stillwater_knot')
    assert (unprotected['focus'],unprotected['last_focus_loss'])==(1,2)
    assert (protected['focus'],protected['last_focus_loss'])==(2,0)
    for action in ['gather','gather','gather']:
        protected=engine.resolve(protected,action)
    assert protected['last_focus_loss']==2 and 0<=protected['focus']<=6
    # A ward is local to its beat, not a permanent saved immunity.
    assert 'focus_ward' not in protected
    ray['focus']=0
    zero=engine.resolve(ray,'gather')
    assert zero['focus']==1 and zero['last_focus_loss']==2
    ray['spells']['stillwater_knot']['effects']=[{'type':'ward_focus','amount':6},{'type':'ward_focus','amount':6}]
    ray['focus']=6
    capped=engine.resolve(ray,'stillwater_knot')
    assert capped['last_focus_loss']==0
    assert 'ward 6' in capped['log'][-1]
    shell=engine.begin('shellfold_sifter',29,['reed_stitch'])
    stitched=engine.resolve(shell,'reed_stitch')
    assert stitched['player_vigor']==30 and stitched['focus']==2

@pytest.mark.parametrize('path,field,value',[
    ('progression/wayfarer.json','level_thresholds',[0,100,100]),
    ('progression/wayfarer.json','level_thresholds',[1,100]),
    ('progression/wayfarer.json','level_thresholds',[0,True]),
    ('progression/wayfarer.json','continued_level_step',0),
    ('progression/wayfarer.json','study_levels',{'affinity':3,'cross_training':2}),
    ('enemies/shellfold_sifter.json','intents',[{'name':'bad','power':4,'guard':True}]),
    ('enemies/hushfin_ray.json','intents',[{'name':'bad','power':4,'focus_drain':7}]),
    ('enemies/hushfin_ray.json','rewards',[{'type':'grant_experience','amount':-1}]),
    ('spells/prism_needle.json','effects',[{'type':'deal_damage','power':9,'piercing':'yes'}]),
    ('spells/stillwater_knot.json','effects',[{'type':'ward_focus','amount':7}]),
])
def test_invalid_authored_progression_and_tactics_fail_before_play(tmp_path,path,field,value):
    root=tmp_path/'content'
    shutil.copytree(ROOT/'content',root)
    file=root/path
    payload=json.loads(file.read_text())
    payload['rules'][field]=value
    file.write_text(json.dumps(payload))
    assert validate_content_tree(root).errors

@pytest.fixture
def old_save(tmp_path,catalog):
    rules=QuestRules(catalog)
    players=VerticalSliceService(JsonVerticalSliceStore(tmp_path/'saved.json'),rules,CharacterProgression(catalog))
    account=players.register('study@example.test','Student','test-only-password').account.id
    character=players.create_character(account,'Student').id
    # An explicit M1.2-shaped old-save fixture; later lessons must still be earned.
    with players.store.transaction(character):
        record=players.enter_world(account,character)
        record.level=2
        record.experience=165
        record.known_spells=BASE.copy()
        record.folio=BASE.copy()
        for key in ['lantern_well_first_light','an_answer_in_the_reeds','reading_the_afterlight','what_the_reeds_hold','a_measured_release']:
            record.quest_state[key]={'completed':True,'state':'completed','rewards_claimed':True}
        players.store.save_character(record)
    return players,StoryService(players,rules),EncounterService(players,CombatEngine(catalog),catalog),account,character

def offer(game,key):
    players,story,_,account,character=game
    view=story.start(account,character,'mara_lanternwright')['dialogue']
    return story.choose(account,character,'mara_lanternwright',view['id'],'study_'+key)

def fight(game,enemy,actions,tag):
    players,_,encounters,account,character=game
    response=encounters.start(account,character,enemy,tag+'-start')
    for index,action in enumerate(actions):
        before=response['encounter']
        response=encounters.act(account,character,before['id'],action,before['round'],tag+f'-action-{index}')
    assert response['encounter']['state']=='victory'
    saved=players.store.path.read_bytes()
    assert encounters.act(account,character,before['id'],actions[-1],before['round'],tag+f'-action-{len(actions)-1}')==response
    assert players.store.path.read_bytes()==saved
    return response

def test_affinity_gates_earned_lessons_cross_training_and_preserved_save(old_save,catalog):
    players,story,encounters,account,character=old_save
    original=players.enter_world(account,character).public_state()
    view=story.start(account,character,'mara_lanternwright')['dialogue']
    assert [o['key'] for o in view['options']]==['study_light_between_plates']
    with pytest.raises(ValueError,match='not available'):
        story.choose(account,character,'mara_lanternwright',view['id'],'study_keep_the_quiet')
    offer(old_save,'light_between_plates')
    result=fight(old_save,'shellfold_sifter',['beacon_trace','glimmer_spark','tide_mend','glimmer_spark','glimmer_spark','tide_mend','beacon_trace','glimmer_spark'],'plates')
    assert result['character']['level']==3 and result['character']['experience']==200
    saved=story.start(account,character,'mara_lanternwright')['character']
    assert saved['experience']==225 and 'prism_needle' in saved['known_spells']
    assert saved['folio']==BASE and saved['appearance']==original['appearance'] and saved['id']==original['id']
    assert not saved['quest_state'].get('keep_the_quiet')
    # Cross-training now opens through the same source and cannot auto-prepare a spell.
    offer(old_save,'keep_the_quiet')
    result=fight(old_save,'hushfin_ray',['beacon_trace','glimmer_spark','gather','tide_mend','glimmer_spark','glimmer_spark'],'quiet')
    saved=story.start(account,character,'mara_lanternwright')['character']
    assert 'stillwater_knot' in saved['known_spells'] and 'stillwater_knot' not in saved['folio']
    assert saved['quest_state']['keep_the_quiet']['rewards_claimed']
    before=deepcopy(saved)
    assert story.start(account,character,'mara_lanternwright')['character']==before
    reloaded=VerticalSliceService(JsonVerticalSliceStore(players.store.path),QuestRules(catalog),CharacterProgression(catalog))
    assert reloaded.enter_world(account,character).public_state()==before
    folio=FolioService(reloaded,catalog)
    with pytest.raises(ValueError,match='between'):
        folio.prepare(account,character,saved['known_spells'],0,'too-many-prepared')

def test_new_encounter_unlocks(old_save):
    players,_,encounters,account,character=old_save
    with players.store.transaction(character):
        record=players.enter_world(account,character)
        record.level=1
        players.store.save_character(record)
    before=players.store.path.read_bytes()
    with pytest.raises(ValueError,match='level 2'):
        encounters.start(account,character,'hushfin_ray','locked-new-enemy')
    assert players.store.path.read_bytes()==before


@pytest.mark.parametrize('affinity,lesson',[
    ('lanterncraft','light_between_plates'),('rootbinding','a_kindly_weave'),('tideseaming','keep_the_quiet')])
def test_each_affinity_has_its_own_early_lesson_and_cross_training_later(old_save,affinity,lesson):
    players,story,_,account,character=old_save
    with players.store.transaction(character):
        record=players.enter_world(account,character)
        record.affinity=affinity
        players.store.save_character(record)
    choices=story.start(account,character,'mara_lanternwright')['dialogue']['options']
    assert [entry['key'] for entry in choices]==['study_'+lesson]
    with players.store.transaction(character):
        record=players.enter_world(account,character)
        record.level=3
        record.experience=200
        players.store.save_character(record)
    choices=story.start(account,character,'mara_lanternwright')['dialogue']['options']
    assert {entry['key'] for entry in choices}=={'study_'+key for key in LESSONS}


def test_catalog_rewards_and_old_active_encounter_defaults(old_save,catalog):
    players,_,encounters,account,character=old_save
    # Existing active payloads have no new armor/drain/ward fields.
    old=encounters.start(account,character,'fog_thorn_lurker','old-active-start')['encounter']
    assert 'guard' not in old['intent'] and 'focus_drain' not in old['intent']
    configured=ContentCatalog.build(ROOT/'content')
    configured.get_definition('enemies','fog_thorn_lurker').rules['rewards']=[
        {'type':'grant_experience','amount':47},{'type':'grant_currency','currency_key':'shell_chits','amount':4}]
    encounters.catalog=configured
    before=players.enter_world(account,character)
    xp,wallet=before.experience,before.wallet['shell_chits']
    for beat in range(1,5):
        result=encounters.act(account,character,old['id'],'glimmer_spark',beat,'old-active-cast-'+str(beat))
    assert result['encounter']['state']=='victory' and result['encounter']['last_focus_loss']==0
    assert result['character']['experience']==xp+47 and result['character']['wallet']['shell_chits']==wallet+4


def test_new_progression_reward_rolls_back_with_failed_save(old_save,monkeypatch):
    players,_,encounters,account,character=old_save
    with players.store.transaction(character):
        record=players.enter_world(account,character)
        record.level=2
        record.encounter=encounters.engine.begin('hushfin_ray',30,BASE)
        record.encounter.update(id='old-active',enemy_vigor=1)
        players.store.save_character(record)
    before=players.store.path.read_bytes()
    def fail(_): raise OSError('isolated save failure')
    monkeypatch.setattr(players.store,'save_character',fail)
    with pytest.raises(OSError):
        encounters.act(account,character,'old-active','glimmer_spark',1,'rollback-new-reward')
    assert players.store.path.read_bytes()==before
