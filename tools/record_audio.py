"""Retain a reviewable recording of the real Godot audio bus, not synthetic flag checks."""
import os
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
def record():
    result=subprocess.run([os.environ.get('GODOT_BIN','godot'),'--headless','--path',str(ROOT/'godot_project'),
        '--script','res://tests/audio_route.gd'],capture_output=True,text=True,timeout=45)
    output=result.stdout+result.stderr
    print(output)
    out=ROOT/'builds/audio-check';out.mkdir(parents=True,exist_ok=True)
    (out/'recording-result.txt').write_text(output)
    assert result.returncode==0 and 'AUDIO_ROUTE_PASS' in output and 'ERROR:' not in output and 'SCRIPT ERROR' not in output
    source=Path.home()/'.local/share/godot/app_userdata/Veilbound Tides/dawnreef-audio-engine.wav'
    assert source.stat().st_size>1_000_000
    shutil.copyfile(source,out/source.name)
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-c:a','libmp3lame','-b:a','128k',str(out/'dawnreef-audio-engine.mp3')],check=True)
if __name__=='__main__':record()
