"""Preview a catalog through the real Godot/API in isolated client data and JSON saves."""
import argparse
import os
import secrets
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import httpx
from tools.author_content import ROOT, create_example, diagnostics
from tools.build_catalog import bundle


def run(content_root=None, interactive=False):
    with tempfile.TemporaryDirectory(prefix='vt-authoring-') as directory:
        work=Path(directory)
        source=content_root or create_example(work/'example')
        report=diagnostics(source)
        if report['errors']:raise ValueError('; '.join(report['errors']))
        project=work/'godot_project'
        shutil.copytree(ROOT/'godot_project',project,ignore=shutil.ignore_patterns('.godot'))
        bundle(source,project/'data/catalog.json')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        base=f'http://127.0.0.1:{port}/api/v1'
        env=dict(os.environ,VT_ENVIRONMENT='local',VT_JWT_SECRET=secrets.token_urlsafe(32),VT_CONTENT_ROOT=str(source.resolve()),VT_PLAYER_STORE='json',VT_VERTICAL_SLICE_SAVE_PATH=str(work/'preview-save.json'),VT_TEST_API_URL=base,XDG_DATA_HOME=str(work/'data'),XDG_CONFIG_HOME=str(work/'config'))
        godot=os.environ.get('GODOT_BIN','godot')
        imported=subprocess.run([godot,'--headless','--editor','--path',str(project),'--quit'],env=env,capture_output=True,text=True,timeout=120)
        if imported.returncode or 'ERROR:' in imported.stdout+imported.stderr:raise RuntimeError(imported.stdout+imported.stderr)
        with (work/'server.log').open('w+') as log:
            server=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=log)
            try:
                with httpx.Client(trust_env=False,timeout=2) as client:
                    for _ in range(60):
                        try:
                            if client.get(base+'/server-info').status_code==200:break
                        except httpx.RequestError:pass
                        time.sleep(.1)
                    else:raise RuntimeError('isolated preview API did not start')
                print('Isolated preview:',base,'; temporary accounts/saves; no live publication.',flush=True)
                script='authoring_interactive.gd' if interactive else 'authoring.gd'
                command=[godot,'--path',str(project),'--script','res://tests/'+script]
                if not interactive:command.insert(1,'--headless')
                try:
                    result=subprocess.run(command,env=env,capture_output=not interactive,text=True,timeout=None if interactive else 120)
                except subprocess.TimeoutExpired as error:
                    print(error.stdout or b'',error.stderr or b'')
                    raise
                if interactive:
                    if result.returncode:raise RuntimeError('preview client failed')
                else:
                    output=result.stdout+result.stderr;print(output)
                    if result.returncode or 'GODOT_AUTHORING_PASS' not in output or 'ERROR:' in output:raise RuntimeError('authoring integration failed')
            finally:
                server.terminate()
                try:server.wait(timeout=10)
                except subprocess.TimeoutExpired:server.kill();server.wait()
                log.seek(0)
                errors=[line for line in log if 'ERROR' in line]
                if errors:print(''.join(errors))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--content-root',type=Path)
    parser.add_argument('--interactive',action='store_true')
    args=parser.parse_args()
    run(args.content_root,args.interactive)
