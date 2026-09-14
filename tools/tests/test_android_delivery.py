"""Reproduce the green-run/missing-APK handoff and reject corrupted packages."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.export_android import ROOT, android_identity
from tools.prepare_android_delivery import prepare_delivery

PRESET = (ROOT / 'godot_project/export_presets.cfg').read_text()


class AndroidDeliveryTests(unittest.TestCase):
    def build(self, directory, architecture='arm64-v8a'):
        folder = Path(directory)
        identity = android_identity(PRESET)
        apk = folder / identity['file']
        with zipfile.ZipFile(apk, 'w') as archive:
            archive.writestr(f'lib/{architecture}/libgodot_android.so', b'test-only packaging fixture')
        manifest = {'source_commit': 'a' * 40, 'tested_tree_commit': 'b' * 40,
                    **{key: identity[key] for key in ('version_name', 'version_code')},
                    'artifacts': [{'file': apk.name, 'architecture': 'arm64',
                                   'bytes': apk.stat().st_size,
                                   'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                                   'signature_verified': True}]}
        (folder / 'build-manifest.json').write_text(json.dumps(manifest))
        apk.with_suffix('.apk.verification.txt').write_text(
            f"package: name='work.surveyroute.veilboundtides' versionCode='{identity['version_code']}' versionName='{identity['version_name']}'\n"
            "sdkVersion:'24'\ntargetSdkVersion:'35'\n"
            'Verified using v2 scheme (APK Signature Scheme v2): true\n'
            'Verified using v3 scheme (APK Signature Scheme v3): true\n')
        return folder, apk, manifest

    def test_version_is_derived_from_named_android_preset(self):
        identity = android_identity(PRESET)
        changed = PRESET.replace(identity['version_name'], '0.9.99')
        self.assertEqual(android_identity(changed)['file'], 'veilbound-tides-0.9.99-android.apk')
        with self.assertRaisesRegex(ValueError, 'export path'):
            android_identity(PRESET.replace('version/name="' + identity['version_name'] + '"', 'version/name="0.9.99"'))

    def test_missing_apk_cannot_publish_evidence_only(self):
        with tempfile.TemporaryDirectory() as directory:
            folder, apk, _ = self.build(directory)
            apk.unlink()
            (folder / 'render-check').mkdir()
            (folder / 'render-check/result.txt').write_text('GODOT_SMOKE_PASS')
            with self.assertRaisesRegex(ValueError, 'missing'):
                prepare_delivery(folder, PRESET)
            self.assertFalse((folder / 'android-delivery').exists())

    def test_stale_export_filename_is_rejected_even_when_present(self):
        with tempfile.TemporaryDirectory() as directory:
            folder, apk, manifest = self.build(directory)
            stale = 'veilbound-tides-0.0.0-android.apk'
            apk.rename(folder / stale)
            manifest['artifacts'][0]['file'] = stale
            (folder / 'build-manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'filename/version'):
                prepare_delivery(folder, PRESET)

    def test_tampering_wrong_abi_and_wrong_report_are_rejected(self):
        for problem in ('hash', 'abi', 'report', 'provenance'):
            with self.subTest(problem=problem), tempfile.TemporaryDirectory() as directory:
                folder, apk, manifest = self.build(directory, 'x86_64' if problem == 'abi' else 'arm64-v8a')
                if problem == 'hash':
                    apk.write_bytes(apk.read_bytes() + b'changed')
                elif problem == 'report':
                    apk.with_suffix('.apk.verification.txt').write_text('wrong version')
                elif problem == 'provenance':
                    manifest.pop('source_commit')
                    (folder / 'build-manifest.json').write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    prepare_delivery(folder, PRESET)

    def test_only_verified_phone_files_are_staged_and_old_output_is_removed(self):
        with tempfile.TemporaryDirectory() as directory:
            folder, apk, _ = self.build(directory)
            (folder / 'veilbound-tides-android-qa.apk').write_bytes(b'not for phones')
            previous = folder / 'android-delivery'
            previous.mkdir()
            (previous / 'stale.apk').write_bytes(b'old')
            destination = prepare_delivery(folder, PRESET)
            self.assertEqual({path.name for path in destination.iterdir()},
                             {apk.name, apk.name + '.verification.txt', 'build-manifest.json'})
            self.assertEqual((destination / apk.name).read_bytes(), apk.read_bytes())


if __name__ == '__main__':
    unittest.main()
