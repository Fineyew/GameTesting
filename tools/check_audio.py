"""Decode the shipped source assets; enforce headroom, loop seams and recorded provenance."""
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def check():
    manifest=json.loads((ROOT/'audio_sources/manifest.json').read_text())
    assert (ROOT/manifest['source']).is_file()
    report=[]; total=0
    for asset in manifest['assets']:
        path=ROOT/asset['file']; total+=path.stat().st_size
        assert hashlib.sha256(path.read_bytes()).hexdigest()==asset['sha256'],path
        result=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar','22050','-'],capture_output=True,check=True)
        samples=array('f',result.stdout)
        assert samples and all(math.isfinite(x) for x in samples),path
        peak=max(abs(x) for x in samples)
        rms=math.sqrt(math.fsum(x*x for x in samples)/len(samples))
        assert .001<rms<.2 and peak<.5,(path,peak,rms)
        assert abs(len(samples)/22050-asset['duration_seconds'])<.01,path
        seam=abs(samples[0]-samples[-1])
        derivative=math.sqrt(math.fsum((a-b)**2 for a,b in zip(samples,samples[1:]))/(len(samples)-1))
        if asset['loop']:
            assert seam<max(.008,3*derivative),(path,'loop boundary',seam,derivative)
        else:
            assert abs(samples[0])<.0001 and abs(samples[-1])<.0001,path
        report.append({'key':asset['key'],'peak':round(peak,6),'rms':round(rms,6),'seam_delta':round(seam,6),'duration':len(samples)/22050})
    assert len(report)==11 and total<600_000,(len(report),total)
    out=ROOT/'builds/audio-check';out.mkdir(parents=True,exist_ok=True)
    source=os.environ.get('VT_SOURCE_COMMIT') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (out/'assets.json').write_text(json.dumps({'source':source,'total_source_bytes':total,'assets':report},indent=2)+'\n')
    print('AUDIO_ASSETS_PASS',total,'bytes;',len(report),'decoded assets with headroom and loop/cue edges')

if __name__=='__main__':check()
