"""Focused content diagnostics and isolated examples; never publish to a live service."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from backend.app.modules.content.service import ContentCatalog
from backend.app.modules.quests.rules import QuestRules
from backend.app.modules.combat.engine import CombatEngine
from tools.build_catalog import bundle

ROOT=Path(__file__).resolve().parents[1]
DEMO='authoring_echo'


def local_path(root,relative):
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('path escapes project root: '+relative)
    return path


def diagnostics(content_root, project_root=ROOT, bindings_path=None):
    """Return deterministic actionable errors/warnings, retaining original catalog validation."""
    errors=[];warnings=[]
    try:
        catalog=ContentCatalog.build(content_root)
        metadata=json.loads((bindings_path or project_root/'authoring/bindings.json').read_text())
        if not isinstance(metadata,dict) or metadata.get('schema')!=1:raise ValueError('unsupported binding schema')
        if not isinstance(metadata.get('asset_references'),dict) or not isinstance(metadata.get('interactions'),dict):
            raise ValueError('asset references and interactions must be objects')
        for quest in catalog.list_definitions('quests'):
            for objective in quest.rules['objectives']:
                if objective['type'] not in QuestRules.SUPPORTED_OBJECTIVES:
                    errors.append(f'quests/{quest.key}/{objective["key"]}: objective has no runtime handler')
        for graph in catalog.list_definitions('dialogue'):
            nodes=graph.rules['nodes']
            pending=[graph.rules['start_node']]+[row['node'] for row in graph.rules.get('entry_nodes',[])]
            seen=set()
            while pending:
                key=pending.pop()
                if key in seen:continue
                seen.add(key)
                pending.extend(o['next_node'] for o in nodes[key].get('options',[]) if o.get('next_node'))
            for key in sorted(set(nodes)-seen):errors.append(f'dialogue/{graph.key}/{key}: unreachable branch')
        references={v for d in catalog.list_definitions() for v in d.assets.values()}
        entries=metadata['asset_references']
        for path in sorted(references-set(entries)):errors.append(f'{path}: missing production status')
        for path in sorted(set(entries)-references):errors.append(f'{path}: stale asset status; no catalog reference')
        for path,entry in sorted(entries.items()):
            if not isinstance(entry,dict):raise ValueError(path+': asset status must be an object')
            if not path.startswith('res://'):raise ValueError('asset must use res://: '+path)
            asset=local_path(project_root/'godot_project',path[6:])
            status=entry.get('status')
            if status not in {'planned','placeholder','candidate','final'}:
                errors.append(f'{path}: invalid asset status');continue
            if status=='planned':
                if not entry.get('reason'):errors.append(f'{path}: planned asset needs a reason')
                warnings.append(f'{path}: planned, not final')
                continue
            if not asset.is_file():errors.append(f'{path}: {status} asset is missing');continue
            if status=='placeholder':
                warnings.append(f'{path}: placeholder, not final');continue
            for field in ('editable_source','license'):
                if not entry.get(field):errors.append(f'{path}: {status} needs {field}')
            if entry.get('editable_source') and not local_path(project_root,entry['editable_source']).is_file():
                errors.append(f'{path}: editable source is missing')
            if status=='final':
                review=entry.get('acceptance_record')
                if not review or not local_path(project_root,review).is_file():
                    errors.append(f'{path}: final requires an acceptance record');continue
                accepted=json.loads(local_path(project_root,review).read_text())
                if accepted.get('asset_sha256')!=hashlib.sha256(asset.read_bytes()).hexdigest() or accepted.get('accepted') is not True or not accepted.get('reviewer'):
                    errors.append(f'{path}: final acceptance does not match this asset')
                for field in ('visual_evidence','device_evidence'):
                    evidence=accepted.get(field)
                    if not evidence or not local_path(project_root,evidence).is_file():errors.append(f'{path}: missing {field}')
        bindings=metadata['interactions']
        bound=set()
        for zone in catalog.list_definitions('zones'):
            for key in zone.rules.get('world',{}).get('interactions',{}):
                bound.add(key)
                row=bindings.get(key)
                if not isinstance(row,dict):errors.append(f'{zone.key}/{key}: missing interaction binding');continue
                handler=row.get('handler')
                if handler=='inspect':
                    if key not in zone.rules.get('discoveries',{}):errors.append(f'{key}: missing discovery')
                elif handler in {'dialogue','encounter'}:
                    category='npcs' if handler=='dialogue' else 'enemies'
                    if row.get('category')!=category or (category,key) not in catalog.definitions:
                        errors.append(f'{key}: invalid {handler} content binding')
                    if key not in zone.rules.get('npcs' if handler=='dialogue' else 'encounters',[]):
                        errors.append(f'{key}: not listed in zone')
                else:errors.append(f'{key}: unsupported interaction handler')
                scene=row.get('scene','')
                if not scene.startswith('res://') or not local_path(project_root/'godot_project',scene[6:]).is_file():errors.append(f'{key}: missing scene binding')
                source=row.get('binding_source','')
                if not source or not local_path(project_root,source).is_file():errors.append(f'{key}: missing binding source')
                handler_source=row.get('handler_source','')
                handler_path=local_path(project_root,handler_source)
                if not handler_source or not handler_path.is_file() or '"'+key+'"' not in handler_path.read_text():
                    errors.append(f'{key}: no declared runtime dispatch; metadata alone cannot add an interaction')
        for key in sorted(set(bindings)-bound):errors.append(f'{key}: dangling interaction binding')
        manifest=json.loads(local_path(project_root,metadata['art_manifest']).read_text())
        if not manifest.get('provenance'):errors.append('art manifest needs provenance')
        for asset in manifest['assets']:
            for field in ('source','recipe'):
                if not local_path(project_root,asset[field]).is_file():errors.append(f'{asset["file"]}: missing {field}')
            runtime=local_path(project_root/'godot_project/assets/dawnreef',asset['file'])
            if not runtime.is_file():errors.append(f'{asset["file"]}: missing runtime export')
        warnings.append('Dawnreef kit remains a candidate; art acceptance and physical validation are separate gates.')
    except (ValueError,RuntimeError,OSError,KeyError,TypeError) as error:
        errors.append(str(error))
    return {'errors':sorted(errors),'warnings':sorted(warnings)}


def create_example(destination, source=ROOT/'content'):
    """Make an editable isolated catalog; do not overwrite source or an existing workspace."""
    if destination.exists():raise ValueError('destination already exists; choose a new authoring workspace')
    if destination.resolve().is_relative_to(source.resolve()) or source.resolve().is_relative_to(destination.resolve()):
        raise ValueError('authoring workspace must be separate from source content')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        draft=Path(temporary)/'content';shutil.copytree(source,draft)
        quest=json.loads((draft/'quests/an_answer_in_the_reeds.json').read_text())
        quest.update(key=DEMO,version=1)
        quest['display']={'name':'A Small Echo','summary':'Listen, then describe what remains.','description':'An isolated authoring example using existing Dawnreef landmarks.'}
        quest['localization']={'en':{'name':'A Small Echo'}}
        quest['rules'].update(start_conditions=[],objectives=[quest['rules']['objectives'][0],quest['rules']['objectives'][2]],rewards=[{'type':'grant_experience','amount':5}])
        write_json(draft/f'quests/{DEMO}.json',quest)
        npc_path=draft/'npcs/mara_lanternwright.json';npc=json.loads(npc_path.read_text())
        npc['version']+=1;npc['rules']['available_quests'].append(DEMO);write_json(npc_path,npc)
        graph_path=draft/'dialogue/mara_first_meeting.json';graph=json.loads(graph_path.read_text());graph['version']+=1
        graph['rules']['entry_nodes'].insert(0,{'node':DEMO,'conditions':[{'type':'quest_state','quest_key':DEMO,'state':'not_started'}]})
        graph['rules']['nodes'][DEMO]={'text':'Before we work, listen to the reeds. Tell me which note stays with you.','options':[{'key':'listen','text':'I will listen.','effects':[{'type':'offer_quest','quest_key':DEMO}]},{'key':'later','text':'Another time.'}]}
        write_json(graph_path,graph)
        report=diagnostics(draft)
        if report['errors']:raise ValueError('; '.join(report['errors']))
        write_json(Path(temporary)/'authoring-preview.json',{'schema':1,'purpose':'isolated authoring example; not live content','quest':DEMO,'source_checksums':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.glob('*/*.json'))}})
        shutil.copytree(temporary,destination)
    return destination/'content'


def write_json(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')


def encounter_preview(content_root,enemy,actions,folio):
    engine=CombatEngine(ContentCatalog.build(content_root))
    state=engine.begin(enemy,30,folio)
    frames=[deepcopy(state)]
    for action in actions:
        if state['state']!='active':raise ValueError('preview encounter already ended')
        state=engine.resolve(state,action);frames.append(deepcopy(state))
    return {'mode':'isolated simulation; no account, rewards or persistence','frames':frames}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    check=commands.add_parser('check');check.add_argument('--content-root',type=Path,default=ROOT/'content')
    example=commands.add_parser('example');example.add_argument('--output',type=Path,required=True)
    combat=commands.add_parser('encounter');combat.add_argument('--content-root',type=Path,default=ROOT/'content');combat.add_argument('--enemy',default='fog_thorn_lurker');combat.add_argument('--actions',default='gather,glimmer_spark');combat.add_argument('--folio',default='glimmer_spark,root_snare,tide_mend')
    args=parser.parse_args()
    try:
        if args.command=='check':
            report=diagnostics(args.content_root);print(json.dumps(report,indent=2));return bool(report['errors'])
        if args.command=='example':print(create_example(args.output));return 0
        print(json.dumps(encounter_preview(args.content_root,args.enemy,args.actions.split(','),args.folio.split(',')),indent=2));return 0
    except (ValueError,RuntimeError,OSError) as error:
        parser.exit(1,str(error)+'\n')

if __name__=='__main__':raise SystemExit(main())
