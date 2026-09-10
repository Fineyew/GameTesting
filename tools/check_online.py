"""Run actual Godot networking against an isolated API and another WebSocket player."""
import asyncio
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import httpx
import websockets

ROOT = Path(__file__).resolve().parents[1]

async def main():
    with tempfile.TemporaryDirectory() as temporary:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0))
            port = probe.getsockname()[1]
        env = dict(os.environ, VT_PLAYER_STORE='json', VT_VERTICAL_SLICE_SAVE_PATH=str(Path(temporary)/'save.json'))
        log = open(Path(temporary)/'server.log','w+')
        server = await asyncio.create_subprocess_exec(sys.executable,'-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port',str(port),cwd=ROOT,env=env,stdout=log,stderr=log)
        try:
            base = f'http://127.0.0.1:{port}/api/v1'
            async with httpx.AsyncClient(trust_env=False) as client:
                for _ in range(80):
                    try:
                        if (await client.get(base+'/server-info')).status_code == 200:
                            break
                    except httpx.RequestError:
                        pass
                    await asyncio.sleep(.1)
                else:
                    raise RuntimeError('API did not start')
                response = await client.post(base+'/auth/register',json={'email':'companion@example.test','display_name':'Companion','password':'test-only-password'})
                response.raise_for_status()
                token = response.json()['access_token']
                response = await client.post(base+'/characters',json={'name':'Companion'},headers={'Authorization':'Bearer '+token})
                response.raise_for_status()
                character_id = response.json()['id']
                async with websockets.connect(f'ws://127.0.0.1:{port}/api/v1/world/socket', proxy=None) as other:
                    await other.send(json.dumps({'type':'auth','protocol':1,'token':token,'character_id':character_id}))
                    assert json.loads(await other.recv())['type']=='welcome'
                    async def keepalive():
                        while True:
                            await other.send('{"type":"ping"}')
                            await asyncio.sleep(3)
                    pulse = asyncio.create_task(keepalive())
                    env['VT_TEST_API_URL'] = base
                    godot = await asyncio.create_subprocess_exec(os.environ.get('GODOT_BIN','godot'),'--headless','--path',str(ROOT/'godot_project'),'--script','res://tests/online.gd',env=env,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
                    communication = asyncio.create_task(godot.communicate())
                    try:
                        output,_ = await asyncio.wait_for(asyncio.shield(communication),180)
                    except TimeoutError:
                        godot.kill()
                        output,_ = await communication
                        print(output.decode())
                        raise
                    finally:
                        pulse.cancel()
                    print(output.decode())
                    assert godot.returncode == 0 and b'GODOT_ONLINE_PASS' in output and b'SCRIPT ERROR' not in output
        finally:
            server.terminate()
            await server.wait()
            log.seek(0)
            output = log.read()
            if 'ERROR' in output:
                print(output)
            log.close()

if __name__ == '__main__':
    asyncio.run(main())
