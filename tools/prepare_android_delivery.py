"""Fail closed on a missing/stale APK; stage only the verified phone deliverable."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from tools.export_android import ROOT, android_identity


def prepare_delivery(build, preset_text):
    build = Path(build)
    identity = android_identity(preset_text)
    manifest = json.loads((build / 'build-manifest.json').read_text())
    records = [record for record in manifest['artifacts'] if record['architecture'] == 'arm64']
    if len(records) != 1:
        raise ValueError('Exactly one verified ARM64 record is required')
    record = records[0]
    if (record['file'] != identity['file'] or manifest.get('version_name') != identity['version_name']
            or manifest.get('version_code') != identity['version_code']):
        raise ValueError('APK filename/version does not match the Android preset')
    for field in ('source_commit', 'tested_tree_commit'):
        if not re.fullmatch(r'[0-9a-f]{40}', manifest.get(field, '')):
            raise ValueError('Missing source/checkout provenance')
    apk = build / identity['file']
    if not apk.is_file():
        raise ValueError('Verified phone APK is missing from the build')
    if (apk.stat().st_size != record['bytes']
            or hashlib.sha256(apk.read_bytes()).hexdigest() != record['sha256']
            or record.get('signature_verified') is not True):
        raise ValueError('Phone APK differs from the verified build')
    with zipfile.ZipFile(apk) as archive:
        if archive.testzip() is not None:
            raise ValueError('APK ZIP checksum failure')
        architectures = {name.split('/')[1] for name in archive.namelist()
                         if name.startswith('lib/') and name.endswith('.so')}
        if architectures != {'arm64-v8a'}:
            raise ValueError('Delivery must contain only ARM64 native libraries')
    report = apk.with_suffix('.apk.verification.txt')
    verification = report.read_text()
    expected = (f"versionCode='{identity['version_code']}'", f"versionName='{identity['version_name']}'",
                "name='work.surveyroute.veilboundtides'", "sdkVersion:'24'", "targetSdkVersion:'35'",
                'Verified using v2 scheme (APK Signature Scheme v2): true',
                'Verified using v3 scheme (APK Signature Scheme v3): true')
    if not all(value in verification for value in expected):
        raise ValueError('Signature/package/version report does not match the delivery')
    # Validate before changing the staging folder. CI upload reads this folder,
    # never a separately hardcoded version or a glob that could include the QA APK.
    destination = build / 'android-delivery'
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir()
    for source in (apk, report, build / 'build-manifest.json'):
        shutil.copy2(source, destination / source.name)
    return destination


if __name__ == '__main__':
    target = prepare_delivery(ROOT / 'builds', (ROOT / 'godot_project/export_presets.cfg').read_text())
    print(f'ANDROID_DELIVERY_PASS: {target.name} contains verified ARM64 APK, report and provenance')
