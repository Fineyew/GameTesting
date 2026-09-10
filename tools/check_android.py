"""Install/start and exercise actual Android touch input/background/resume using adb.
Requires an already booted emulator/device; x86_64 QA APK is NOT the ARM64 deliverable.
"""
import re
import subprocess
import time
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'builds/android-check'
PACKAGE='work.surveyroute.veilboundtides'

def adb(*args,binary=False):
    return subprocess.check_output(['adb',*args],timeout=40,text=not binary)

def wait_for(check,seconds=30):
    until=time.monotonic()+seconds
    while time.monotonic()<until:
        if check():return
        time.sleep(.5)
    raise AssertionError('Android condition timed out')

def capture(name):
    path=OUT/(name+'.png')
    path.write_bytes(adb('exec-out','screencap','-p',binary=True))
    return path

def wait_for_world(name):
    # Engine-ready logging precedes shader compilation/presentation on software GPUs.
    # Require the authored green terrain (not the gray splash or a black resume frame).
    def visible():
        with Image.open(capture(name)) as frame:
            # Android can present a rotated transition frame after returning from
            # its portrait launcher. Wait for the app's landscape surface before
            # comparing it; never rotate evidence or relax the world-match gate.
            if frame.width <= frame.height:
                return False
            pixels=list(frame.convert('RGB').resize((160,90)).getdata())
        green=sum(g>r*1.12 and g>b*1.08 and g>65 for r,g,b in pixels)/len(pixels)
        return green>.03
    wait_for(visible,45)
    return OUT/(name+'.png')

def changed_world(left_path,right_path):
    with Image.open(left_path) as left,Image.open(right_path) as right:
        width,height=left.size
        region=(int(width*.3),int(height*.22),int(width*.7),int(height*.66))
        difference=ImageChops.difference(left.convert('RGB').crop(region),right.convert('RGB').crop(region)).convert('L')
        histogram=difference.histogram()
        return sum(histogram[13:])/sum(histogram)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    adb('shell','wm','size','720x1280')
    adb('shell','settings','put','system','accelerometer_rotation','0')
    adb('shell','settings','put','system','user_rotation','1')
    # Dismiss the OS tutorial in the test profile; this is not an app permission.
    adb('shell','settings','put','secure','immersive_mode_confirmations','confirmed')
    adb('install','-r',str(ROOT/'builds/veilbound-tides-android-qa.apk'))
    adb('logcat','-c')
    adb('shell','monkey','-p',PACKAGE,'-c','android.intent.category.LAUNCHER','1')
    def log():return adb('logcat','-d','-s','godot:V','AndroidRuntime:E','libc:F')
    wait_for(lambda:'VT_GATEWAY_READY' in log())
    gateway=wait_for_world('gateway')
    assert 'ERROR:' not in log(), 'Godot engine/render error; inspect android-check/logcat.txt'
    with Image.open(gateway) as image:width,height=image.size
    assert width>height,'expected landscape'
    # Real touch on the current 1280x720 logical preview button, then joystick drag.
    adb('shell','input','tap',str(round(width*.80)),str(round(height*.83)))
    wait_for(lambda:'VT_PREVIEW_READY' in log())
    before=wait_for_world('dawnreef-before')
    adb('shell','input','tap',str(round(width*.766)),str(round(height*.075)))
    wait_for(lambda:'VT_FOLIO_READY' in log())
    # Capture the actual touch-opened folio, then close with its touch target.
    time.sleep(.5)
    folio=capture('folio')
    assert changed_world(before,folio)>.1,'folio panel did not visibly open'
    adb('shell','input','tap',str(round(width*.715)),str(round(height*.167)))
    wait_for(lambda:changed_world(before,capture('folio-closed'))<.15)
    adb('shell','input','swipe',str(round(width*.0875)),str(round(height*.844)),str(round(width*.0875)),str(round(height*.755)),'1800')
    time.sleep(.5)
    after=wait_for_world('dawnreef-after')
    changed=changed_world(before,after)
    assert changed>.025,f'touch movement did not visibly change world: {changed}'
    adb('shell','input','keyevent','KEYCODE_HOME')
    time.sleep(1)
    adb('shell','monkey','-p',PACKAGE,'-c','android.intent.category.LAUNCHER','1')
    assert adb('shell','pidof',PACKAGE).strip(),'process missing after resume'
    resumed=wait_for_world('resumed')
    assert changed_world(after,resumed)<.15,'world view changed unexpectedly across resume'
    adb('shell','input','swipe',str(round(width*.0875)),str(round(height*.844)),str(round(width*.125)),str(round(height*.844)),'1800')
    time.sleep(.5)
    resumed_move=wait_for_world('resumed-moved')
    assert changed_world(resumed,resumed_move)>.025,'touch locomotion failed after resume'
    logs=log()
    (OUT/'logcat.txt').write_text(logs)
    assert not re.search(r'ERROR:|SCRIPT ERROR|FATAL EXCEPTION|Fatal signal|ANR in '+re.escape(PACKAGE),logs),logs[-6000:]
    (OUT/'result.txt').write_text(f'ANDROID_RUNTIME_PASS\nInstall, visible gateway, touch preview, touch folio open/close, touch locomotion, background/resume with landscape visible world and repeat touch locomotion.\nChanged world pixels: {changed:.3f}\nEmulator x86_64; physical ARM64 device unverified.\n')
    print('ANDROID_RUNTIME_PASS')

if __name__=='__main__':
    try:
        main()
    finally:
        OUT.mkdir(parents=True,exist_ok=True)
        try:
            (OUT/'logcat.txt').write_text(adb('logcat','-d','-s','godot:V','AndroidRuntime:E','libc:F'))
        except (OSError,subprocess.SubprocessError):
            pass
