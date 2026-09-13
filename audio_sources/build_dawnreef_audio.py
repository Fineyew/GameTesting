"""Original Dawnreef motif, sound bed and small cue set. No external recordings.
Authoring only: Python + NumPy + FFmpeg. Runtime consumes the exported assets.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import tempfile
import wave
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'godot_project/audio'
RATE=22050
RNG=np.random.default_rng(73194)
records=[]


def hz(note): return 440*2**((note-69)/12)


def bell(note, duration=2.5):
    t=np.arange(round(duration*RATE))/RATE
    attack=1-np.exp(-t*70)
    signal=sum(weight*np.sin(2*np.pi*hz(note)*ratio*t)*np.exp(-t/decay)
               for ratio,weight,decay in [(1,1,1.1),(2.01,.25,.6),(3.98,.09,.25)])
    return signal*attack*np.minimum(1,(duration-t)/.12)


def add_loop(target, sound, at, amount=1):
    indices=(np.arange(len(sound))+round(at*RATE))%len(target)
    np.add.at(target,indices,sound*amount)


def write(name, signal, loop=False, bus='Spells', caption=''):
    signal=signal-np.mean(signal)
    peak=float(np.max(np.abs(signal)))
    limit=.32 if loop else .46
    signal*=min(1,limit/max(peak,.00001))
    if not loop:
        n=min(len(signal)//3,round(RATE*.008))
        signal[:n]*=np.linspace(0,1,n)
        signal[-n:]*=np.linspace(1,0,n)
    pcm=np.round(np.clip(signal,-1,1)*32767).astype('<i2')
    extension='.ogg' if loop else '.wav'
    path=OUT/(name+extension)
    with tempfile.TemporaryDirectory() as tmp:
        raw=Path(tmp)/'source.wav'
        with wave.open(str(raw),'wb') as stream:
            stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(RATE);stream.writeframes(pcm.tobytes())
        if loop:
            subprocess.run(['ffmpeg','-v','error','-y','-fflags','+bitexact','-i',str(raw),'-map_metadata','-1',
                '-c:a','libvorbis','-q:a','4','-flags:a','+bitexact',str(path)],check=True)
        else:
            path.write_bytes(raw.read_bytes())
    records.append({'key':name,'file':str(path.relative_to(ROOT)),'loop':loop,'bus':bus,'caption':caption,
        'duration_seconds':round(len(pcm)/RATE,5),'sample_rate':RATE,'channels':1,'source_peak':round(float(np.max(np.abs(signal))),5),
        'source_rms':round(float(np.sqrt(np.mean(signal**2))),5),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Eight bars at80 BPM. This exact melody/harmony is composed for Dawnreef.
    music=np.zeros(RATE*24)
    melody=[74,69,76,72,79,76,74,67,72,69,77,76,74,81,79,76]
    chords=[(50,57,60,64),(55,62,65,69),(48,55,62,64),(57,60,64,67)]
    for i,note in enumerate(melody): add_loop(music,bell(note),i*1.5,.11)
    for i,chord in enumerate(chords):
        t=np.arange(RATE*8)/RATE
        env=np.sin(np.pi*t/8)**2
        pad=sum((np.sin(2*np.pi*hz(n)*t)+.12*np.sin(2*np.pi*hz(n)*2*t)) for n in chord)*env*.018
        add_loop(music,pad,i*6-1)
    write('dawnreef_theme',music,True,'Music')
    # A quieter related pulse crossfades into Tidebeat; it never dictates turn timing.
    battle=music*.45
    for beat in range(32):
        t=np.arange(round(RATE*.65))/RATE
        pulse=np.sin(2*np.pi*hz(chords[beat//8][0])*t)*np.exp(-t*7)*(1-np.exp(-t*90))
        add_loop(battle,pulse,beat*.75,.14 if beat%4==0 else .08)
        if beat%2==1: add_loop(battle,bell(62+(beat%3)*5,1.5),beat*.75,.055)
    write('tidebeat_theme',battle,True,'Music')
    # Periodic filtered noise has continuous wraparound and no sampled recordings.
    n=RATE*16
    noise=RNG.normal(size=n)
    freq=np.fft.rfftfreq(n,1/RATE)
    spectrum=np.fft.rfft(noise)
    filtered=np.fft.irfft(spectrum/np.maximum(freq,35)**.7,n=n)
    filtered=filtered/max(np.std(filtered),.000001)
    t=np.arange(n)/RATE
    wind=filtered*(.018+.006*np.sin(2*np.pi*t/16)+.004*np.cos(2*np.pi*t/8))
    for at,note in [(2.2,86),(7.1,81),(12.4,88)]: add_loop(wind,bell(note),at,.01)
    write('reef_wind',wind,True,'Ambience')
    write('ui',bell(81,.16)*.16,caption='Soft button chime',bus='UI')
    t=np.arange(round(RATE*.18))/RATE
    foot=(RNG.normal(size=len(t))*.22+np.sin(2*np.pi*155*t))*.30*np.exp(-t*28)
    write('footstep',foot,bus='Movement',caption='Footsteps')
    cast=bell(74,1.0)*.17
    cast+=bell(81,1.0)*.11
    write('cast',cast,caption='A lens gathers light')
    t=np.arange(round(RATE*.36))/RATE
    hit=(RNG.normal(size=len(t))*.22+np.sin(2*np.pi*(130*t-80*t*t)))*np.exp(-t*14)*.32
    write('impact',hit,caption='A spell strikes')
    write('mend',bell(76,1.2)*.18+bell(81,1.2)*.14,caption='A warm seam closes')
    write('guard',bell(62,.8)*.23+bell(69,.8)*.10,caption='A protective weave settles')
    t=np.arange(round(RATE*.65))/RATE
    rustle=(RNG.normal(size=len(t))*.14+np.sin(2*np.pi*(75*t+17*t*t))*.4)*np.sin(np.pi*t/.65)**2*.32
    write('creature',rustle,bus='Creatures',caption='The fog-thorn lurker stirs')
    write('discovery',bell(74,1.6)*.14+bell(81,1.6)*.12+bell(86,1.6)*.06,bus='UI',caption='A clear discovery chime')
    manifest={'revision':1,'status':'original audio sample candidate; owner and physical-device listening pending',
        'source':'audio_sources/build_dawnreef_audio.py','provenance':'Original composition and mathematical synthesis for Veilbound Tides. No external recordings, voices, sample packs or generated-service assets.',
        'rights':'Project-authored source and assets; no third-party recording license required.',
        'assets':records}
    (ROOT/'audio_sources/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('DAWNREEF_AUDIO_AUTHORED',len(records),'assets',sum((ROOT/r['file']).stat().st_size for r in records),'bytes')

if __name__=='__main__': main()
