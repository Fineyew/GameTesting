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

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    adb('shell','wm','size','720x1280')
    adb('shell','settings','put','system','accelerometer_rotation','0')
    adb('shell','settings','put','system','user_rotation','1')
    adb('install','-r',str(ROOT/'builds/veilbound-tides-android-qa.apk'))
    adb('logcat','-c')
    adb('shell','monkey','-p',PACKAGE,'-c','android.intent.category.LAUNCHER','1')
    def log():return adb('logcat','-d','-s','godot:V','AndroidRuntime:E','libc:F')
    wait_for(lambda:'VT_GATEWAY_READY' in log())
    time.sleep(2)
    gateway=capture('gateway')
    with Image.open(gateway) as image:width,height=image.size
    assert width>height,'expected landscape'
    # Real touch on the current 1280x720 logical preview button, then joystick drag.
    adb('shell','input','tap',str(round(width*.80)),str(round(height*.83)))
    wait_for(lambda:'VT_PREVIEW_READY' in log())
    time.sleep(1)
    before=capture('dawnreef-before')
    adb('shell','input','swipe',str(round(width*.0875)),str(round(height*.844)),str(round(width*.0875)),str(round(height*.755)),'1800')
    time.sleep(.5)
    after=capture('dawnreef-after')
    region=(int(width*.3),int(height*.22),int(width*.7),int(height*.66))
    with Image.open(before) as left,Image.open(after) as right:
        difference=ImageChops.difference(left.convert('RGB').crop(region),right.convert('RGB').crop(region)).convert('L')
        histogram=difference.histogram()
        changed=sum(histogram[13:])/sum(histogram)
    assert changed>.025,f'touch movement did not visibly change world: {changed}'
    adb('shell','input','keyevent','KEYCODE_HOME')
    time.sleep(1)
    adb('shell','monkey','-p',PACKAGE,'-c','android.intent.category.LAUNCHER','1')
    time.sleep(2)
    assert adb('shell','pidof',PACKAGE).strip(),'process missing after resume'
    capture('resumed')
    logs=log()
    (OUT/'logcat.txt').write_text(logs)
    assert not re.search(r'SCRIPT ERROR|FATAL EXCEPTION|Fatal signal|ANR in '+re.escape(PACKAGE),logs),logs[-6000:]
    (OUT/'result.txt').write_text(f'ANDROID_RUNTIME_PASS\nInstall, gateway, touch preview, touch locomotion, background/resume.\nChanged world pixels: {changed:.3f}\nEmulator x86_64; physical ARM64 device unverified.\n')
    print('ANDROID_RUNTIME_PASS')

if __name__=='__main__':main()
