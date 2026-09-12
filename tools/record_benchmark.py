"""Record matching actual-engine before/after art routes, not real-time performance evidence."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'de9d7a38bed6c18b396173cfd926c09c20e8159d'
GODOT = os.environ.get('GODOT_BIN','godot')
DESTINATION = ROOT/'builds/render-check'


def run(args, timeout=180):
    result = subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    output = result.stdout+result.stderr
    print(output)
    assert result.returncode == 0 and 'ERROR:' not in output and 'SCRIPT ERROR' not in output
    return output


def record(project, name):
    movie = DESTINATION/(name+'.ogv')
    output = run([GODOT,'--path',str(project),'--resolution','1280x720','--write-movie',str(movie),
        '--fixed-fps','30','--script','res://tests/benchmark_route.gd'])
    assert 'BENCHMARK_ROUTE_PASS' in output and movie.stat().st_size > 100_000
    run(['ffmpeg','-y','-i',str(movie),'-an','-c:v','libx264','-crf','22','-pix_fmt','yuv420p',
         '-movflags','+faststart',str(DESTINATION/(name+'.mp4'))])
    movie.unlink()


def main():
    DESTINATION.mkdir(parents=True,exist_ok=True)
    # A shallow CI checkout needs the named preserved baseline. Never switch its HEAD.
    present = subprocess.run(['git','cat-file','-e',BASELINE],cwd=ROOT,capture_output=True)
    if present.returncode:
        subprocess.run(['git','fetch','--depth=1','origin',BASELINE],cwd=ROOT,check=True)
    with tempfile.TemporaryDirectory() as temporary:
        old = Path(temporary)
        archive = subprocess.check_output(['git','archive',BASELINE,'godot_project'],cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(archive)) as content:
            content.extractall(old,filter='data')
        shutil.copy2(ROOT/'godot_project/tests/benchmark_route.gd',old/'godot_project/tests/benchmark_route.gd')
        run([GODOT,'--headless','--editor','--path',str(old/'godot_project'),'--quit'])
        record(old/'godot_project','before-m13')
    record(ROOT/'godot_project','after-m14')
    source = os.environ.get('VT_SOURCE_COMMIT') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (DESTINATION/'walkthrough.json').write_text(json.dumps({'before':BASELINE,'after':source,
        'route':'godot_project/tests/benchmark_route.gd','viewport':[1280,720],'render_scale':.75,
        'shadows':False,'capture_fps':30,'mode':'Godot Movie Maker, offline preview; not real-time/device performance'},indent=2)+'\n')


if __name__ == '__main__':
    main()
