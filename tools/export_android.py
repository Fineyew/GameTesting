"""Reproducible debug export using installed SDK35/JDK17 and Godot4.5.1 templates.
Creates an ARM64 deliverable plus an optional x86_64 emulator-only build. No release
keystore or production secret is used. Runtime configuration is outside the repository.
"""
import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GODOT = os.environ.get('GODOT_BIN','godot')
BUILD = ROOT / 'builds'


def android_identity(preset_text):
    """Use the named Android preset as the single version/filename source."""
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(preset_text)
    sections = [section for section in config.sections()
                if config.get(section, 'name', fallback='') == '"Android"'
                and config.get(section, 'platform', fallback='') == '"Android"']
    if len(sections) != 1:
        raise ValueError('Exactly one named Android export preset is required')
    section = sections[0]
    options = config[section + '.options']
    version = json.loads(options['version/name'])
    code = int(options['version/code'])
    if not isinstance(version, str) or not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version) or code < 1:
        raise ValueError('Invalid Android version name/code')
    filename = f'veilbound-tides-{version}-android.apk'
    if json.loads(config[section]['export_path']) != '../builds/' + filename:
        raise ValueError('Android export path must match its version name')
    return {'version_name': version, 'version_code': code, 'file': filename}


def run(args, **kwargs):
    result = subprocess.run(args,capture_output=True,text=True,timeout=240,**kwargs)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    if result.returncode or 'SCRIPT ERROR' in result.stdout+result.stderr:
        raise RuntimeError(f'command failed: {args[0]}')
    return result.stdout


def export(emulator=False):
    SDK = Path(os.environ['ANDROID_HOME'])
    JAVA = Path(os.environ['JAVA_HOME'])
    preset = ROOT/'godot_project/export_presets.cfg'
    original = preset.read_text()
    identity = android_identity(original)
    BUILD.mkdir(exist_ok=True)
    run([GODOT,'--headless','--editor','--path',str(ROOT/'godot_project'),'--quit'])
    settings = Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'godot/editor_settings-4.5.tres'
    text = settings.read_text()
    for key,value in [('export/android/android_sdk_path',SDK),('export/android/java_sdk_path',JAVA)]:
        line = f'{key} = "{value}"'
        pattern = '^'+re.escape(key)+' = .*$'
        text = re.sub(pattern,lambda match:line,text,flags=re.M) if re.search(pattern,text,re.M) else text+'\n'+line+'\n'
    settings.write_text(text)
    key = BUILD/'debug.keystore'
    if not key.exists():
        run([str(JAVA/'bin/keytool'),'-genkeypair','-keystore',str(key),'-storepass','android','-alias','androiddebugkey','-keypass','android','-dname','CN=Android Debug,O=Android,C=US','-keyalg','RSA','-keysize','2048','-validity','10000'])
    env = dict(os.environ,GODOT_ANDROID_KEYSTORE_DEBUG_PATH=str(key),GODOT_ANDROID_KEYSTORE_DEBUG_USER='androiddebugkey',GODOT_ANDROID_KEYSTORE_DEBUG_PASSWORD='android')
    records=[]
    try:
        targets=[('arm64',identity['file'],original)]
        if emulator:
            targets.append(('x86_64-emulator-only','veilbound-tides-android-qa.apk',original.replace('architectures/arm64-v8a=true','architectures/arm64-v8a=false').replace('architectures/x86_64=false','architectures/x86_64=true')))
        for architecture,filename,configuration in targets:
            preset.write_text(configuration)
            target=BUILD/filename
            run([GODOT,'--headless','--path',str(ROOT/'godot_project'),'--export-debug','Android',str(target)],env=env)
            signature=run([str(SDK/'build-tools/35.0.0/apksigner'),'verify','--verbose',str(target)])
            badging=run([str(SDK/'build-tools/35.0.0/aapt'),'dump','badging',str(target)])
            assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in signature
            assert "name='work.surveyroute.veilboundtides'" in badging
            assert f"versionCode='{identity['version_code']}'" in badging
            assert f"versionName='{identity['version_name']}'" in badging
            assert "sdkVersion:'24'" in badging and "targetSdkVersion:'35'" in badging
            (BUILD/(filename+'.verification.txt')).write_text(signature+'\n'+badging)
            records.append({'file':filename,'architecture':architecture,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'signature_verified':True,'min_sdk':24,'target_sdk':35})
    finally:
        preset.write_text(original)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    manifest={'source_commit':os.environ.get('VT_SOURCE_COMMIT',commit),'tested_tree_commit':commit,'godot':'4.5.1','version_name':identity['version_name'],'version_code':identity['version_code'],'signing':'ephemeral debug identity; not a release key','artifacts':records}
    (BUILD/'build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('ANDROID_EXPORT_PASS')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--emulator',action='store_true')
    export(parser.parse_args().emulator)
