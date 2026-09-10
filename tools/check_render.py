"""Render actual Godot frames under a display; retain evidence and a bounded draw-count gate."""
import os
from pathlib import Path
import re
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
result=subprocess.run([os.environ.get('GODOT_BIN','godot'),'--path',str(ROOT/'godot_project'),'--audio-driver','Dummy','--script','res://tests/smoke.gd'],capture_output=True,text=True,timeout=60)
output=result.stdout+result.stderr
print(output)
assert result.returncode==0 and 'GODOT_SMOKE_PASS' in output and 'ERROR:' not in output and 'SCRIPT ERROR' not in output
calls=int(re.search(r'DRAW_CALLS=(\d+)',output).group(1))
assert calls<=150,f'default scene exceeded draw-call budget: {calls}'
primitives=int(re.search(r'RENDERED_PRIMITIVES=(\d+)',output).group(1))
textures=int(re.search(r'TEXTURE_BYTES=(\d+)',output).group(1))
assert primitives<=150_000,f'default scene exceeded triangle/primitive budget: {primitives}'
assert textures<=128*1024*1024,f'initial texture budget exceeded: {textures}'
destination=ROOT/'builds/render-check'
destination.mkdir(parents=True,exist_ok=True)
source=Path.home()/'.local/share/godot/app_userdata/Veilbound Tides'
for name in ['gateway.png','dawnreef.png','folio.png','vendor.png','equipment.png','benchmark.png','mara.png','wayfarer.png','glimmer.png']:
    shutil.copy2(source/name,destination/name)
(destination/'result.txt').write_text(output)
