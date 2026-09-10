"""Godot can exit zero after script errors; require an explicit smoke success marker."""
import os
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
godot = os.environ.get('GODOT_BIN','godot')
for args, marker in [(['--editor','--quit'],None),(['--script','res://tests/smoke.gd'],'GODOT_SMOKE_PASS')]:
    result = subprocess.run([godot,'--headless','--path',str(ROOT/'godot_project'),*args],capture_output=True,text=True,timeout=60)
    output = result.stdout + result.stderr
    print(output)
    if result.returncode or 'ERROR:' in output or 'SCRIPT ERROR' in output or (marker and marker not in output):
        raise SystemExit(1)
