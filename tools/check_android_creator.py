"""Actual native creator input against a disposable loopback API, never a public server."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import httpx
from PIL import Image, ImageChops
from tools.check_android import (ROOT, OUT, PACKAGE, adb, capture, wait_for, wait_for_world,
                                wait_for_settled_world, changed_world, wait_for_input_ready, dismiss_keyboard)


def check_creator():
    def log():
        return adb('logcat', '-d', '-s', 'godot:V', 'AndroidRuntime:E', 'libc:F')

    def layout():
        records = [line.split('VT_GATEWAY_LAYOUT=', 1)[1] for line in log().splitlines()
                   if 'VT_GATEWAY_LAYOUT=' in line]
        return json.loads(records[-1]) if records else {'controls': {}}

    with Image.open(OUT / 'gateway.png') as image:
        width, height = image.size

    def rect(label):
        wait_for(lambda: label in layout()['controls'])
        view = layout()
        x, y, w, h = view['controls'][label]
        sx, sy = width / view['width'], height / view['height']
        assert x >= 0 and y >= 0 and x + w <= view['width'] and y + h <= view['height']
        return tuple(round(v) for v in (x * sx, y * sy, (x + w) * sx, (y + h) * sy))

    def tap(label):
        x0, y0, x1, y1 = rect(label)
        adb('shell', 'input', 'tap', str((x0 + x1) // 2), str((y0 + y1) // 2))

    def fill(label, value):
        tap(label)
        # Ordinary native keyboard editing also replaces the prefilled server URL.
        adb('shell', 'input', 'keycombination', 'KEYCODE_CTRL_LEFT', 'KEYCODE_A')
        adb('shell', 'input', 'keyevent', 'KEYCODE_DEL')
        adb('shell', 'input', 'text', value)
        dismiss_keyboard()

    def changed(left, right, region):
        with Image.open(left) as a, Image.open(right) as b:
            diff = ImageChops.difference(a.convert('RGB').crop(region), b.convert('RGB').crop(region)).convert('L')
            counts = diff.histogram()
            return sum(counts[14:]) / sum(counts)

    with tempfile.TemporaryDirectory(prefix='vt-native-creator-') as directory:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        env = dict(os.environ, VT_ENVIRONMENT='local', VT_PLAYER_STORE='json',
                   VT_JWT_SECRET=secrets.token_urlsafe(48),
                   VT_VERTICAL_SLICE_SAVE_PATH=str(Path(directory) / 'save.json'))
        with (OUT / 'creator-server.log').open('w') as server_log:
            server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.app.main:app',
                                       '--host', '127.0.0.1', '--port', str(port)],
                                      cwd=ROOT, env=env, stdout=server_log, stderr=server_log)
            reverse = f'tcp:{port}'
            try:
                base = f'http://127.0.0.1:{port}/api/v1'
                with httpx.Client(trust_env=False, timeout=5) as client:
                    def ready():
                        try:
                            return client.get(base + '/server-info').status_code == 200
                        except httpx.RequestError:
                            return False
                    wait_for(ready)
                    account = {'email': 'native@example.test', 'display_name': 'Native tester',
                               'password': 'native-test-password'}
                    registration = client.post(base + '/auth/register', json=account)
                    registration.raise_for_status()
                    headers = {'Authorization': 'Bearer ' + registration.json()['access_token']}
                    adb('reverse', reverse, reverse)
                    adb('shell', 'am', 'force-stop', PACKAGE)
                    adb('shell', 'monkey', '-p', PACKAGE, '-c', 'android.intent.category.LAUNCHER', '1')
                    wait_for_world('gateway')
                    wait_for_input_ready()
                    # Use real form navigation and text input; no auth or UI bypass.
                    if 'Server connection' not in layout()['controls']:
                        adb('shell', 'input', 'swipe', str(round(width*.8)), str(round(height*.83)),
                            str(round(width*.8)), str(round(height*.55)), '500')
                    tap('Server connection')
                    fill('https://server.example/api/v1', base)
                    tap('Save connection')
                    fill('Email address', account['email'])
                    fill('Password', account['password'])
                    tap('Sign in')
                    wait_for(lambda: 'VT_CREATOR_READY' in log())
                    region = rect('avatar')
                    before = capture('creator-native-default')
                    tap('Reef teal robe')
                    # Touch-opened Godot menus start with no keyboard focus (-1).
                    # First Down focuses item 0; second Down reaches item 1.
                    adb('shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN', 'KEYCODE_DPAD_DOWN')
                    adb('shell', 'input', 'keyevent', 'KEYCODE_ENTER')
                    wait_for(lambda: 'VT_CREATOR_COLORS=coral,warm' in log())
                    tap('Warm skin')
                    adb('shell', 'input', 'keyevent', 'KEYCODE_DPAD_DOWN', 'KEYCODE_DPAD_DOWN')
                    adb('shell', 'input', 'keyevent', 'KEYCODE_ENTER')
                    wait_for(lambda: 'VT_CREATOR_COLORS=coral,deep' in log())
                    wait_for(lambda: changed(before, capture('creator-native-colors'), region) > .015)
                    colored = OUT / 'creator-native-colors.png'
                    x0, y0, x1, y1 = region
                    adb('shell', 'input', 'swipe', str((x0+x1)//2), str((y0+y1)//2),
                        str((x0+x1)//2+80), str((y0+y1)//2), '600')
                    wait_for(lambda: changed(colored, capture('creator-native-rotated'), region) > .015)
                    tap('Front')
                    fill('Character name · 2–24 characters', 'NativeWayfarer')
                    if 'Create Wayfarer' not in layout()['controls']:
                        adb('shell', 'input', 'swipe', str(round(width*.85)), str(round(height*.8)),
                            str(round(width*.85)), str(round(height*.55)), '500')
                    tap('Create Wayfarer')
                    rect('Enter Dawnreef')
                    capture('creator-native-saved')
                    saved = client.get(base + '/characters', headers=headers)
                    saved.raise_for_status()
                    # The HTTP route returns a list; only Godot's ApiClient wraps
                    # list responses in its internal {data: ...} convenience shape.
                    character = saved.json()[0]
                    assert character['appearance'] == {'robe': 'coral', 'skin': 'deep'}
                    tap('Enter Dawnreef')
                    # This marker requires the actual socket welcome, our first
                    # authoritative snapshot and the player-follow camera.
                    wait_for(lambda: 'VT_ONLINE_READY' in log(), 45)
                    before_world = wait_for_settled_world('creator-native-world')
                    wait_for_input_ready()
                    adb('shell', 'input', 'swipe', str(round(width*.0875)), str(round(height*.844)),
                        str(round(width*.155)), str(round(height*.844)), '1000')
                    moved_world = wait_for_settled_world('creator-native-moved')
                    assert changed_world(before_world, moved_world) > .025, 'Online touch did not visibly move the world'
                    logs = log()
                    assert 'ERROR:' not in logs and 'SCRIPT ERROR' not in logs
                    (OUT / 'creator-result.txt').write_text(
                        'ANDROID_CREATOR_PASS\nLoopback login, touch-opened color menus with keyboard selection, '
                        'visible tint changes, touch drag/front reset, native creation, saved appearance, '
                        'socket welcome/authoritative snapshot, settled player camera and visible online touch movement.\n'
                        'Emulator only; physical phone/safe-cutout/thermal acceptance remains open.\n')
                    print('ANDROID_CREATOR_PASS')
            except BaseException:
                # Retain the actual failure before force-stop changes the screen.
                capture('creator-failed')
                (OUT / 'creator-failed-window.txt').write_text(adb('shell', 'dumpsys', 'window'))
                (OUT / 'creator-failed-layout.json').write_text(json.dumps(layout(), indent=2))
                raise
            finally:
                # Stop the client before removing its disposable API; preserve earlier native logs.
                adb('shell', 'am', 'force-stop', PACKAGE)
                subprocess.run(['adb', 'reverse', '--remove', reverse], capture_output=True, timeout=10)
                server.terminate()
                server.wait(timeout=10)
