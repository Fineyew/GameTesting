"""API35 readiness: laid-out frame, focused surface and bounded stabilization."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools import check_android as gate

APP = 'Window{test u0 work.surveyroute.veilboundtides/com.godot.game.GodotApp}'
READY = f'''  mCurrentFocus={APP}
  no ScreenRotationAnimation
  Window #7 {APP}:
    Requested w=1280 h=720
    mViewVisibility=0x0 mHaveFrame=true mObscured=false
    mHasSurface=true isReadyForDisplay()=true mWindowRemovalAllowed=false
    Frames: parent=[0,0][1280,720] display=[0,0][1280,720] frame=[0,0][1280,720] last=[0,0][1280,720]
      Surface: shown=true    mForceSeamlesslyRotate=false seamlesslyRotate: pending=null
    isVisible=true
  Window #8 Window{{other u0 com.android.launcher/Home}}:
    Requested w=1280 h=720
    mViewVisibility=0x0 mHaveFrame=true
    mHasSurface=true isReadyForDisplay()=true
    Frames: parent=[0,0][1280,720] display=[0,0][1280,720] frame=[0,0][1280,720] last=[0,0][1280,720]
      Surface: shown=true
    isVisible=true
'''

class AndroidWindowTests(unittest.TestCase):
    def test_hidden_keyboard_never_sends_back(self):
        for state in ('mIsImeShowing=false', ''):
            with patch.object(gate, 'adb', return_value=state) as adb:
                gate.dismiss_keyboard()
            adb.assert_called_once_with('shell', 'dumpsys', 'window')

    def test_visible_keyboard_is_dismissed_once_and_waited_for(self):
        states = iter(['mIsImeShowing=true', 'mIsImeShowing=true', 'mIsImeShowing=false'])
        calls = []
        def adb(*args):
            calls.append(args)
            return next(states) if args == ('shell', 'dumpsys', 'window') else ''
        with patch.object(gate, 'adb', adb), patch.object(gate.time, 'sleep'):
            gate.dismiss_keyboard()
        self.assertEqual(calls.count(('shell', 'input', 'keyevent', 'KEYCODE_BACK')), 1)
        self.assertEqual(calls[-1], ('shell', 'dumpsys', 'window'))

    def test_actual_api35_shape_without_legacy_transition_field(self):
        self.assertTrue(gate.input_window_ready(READY))

    def test_landscape_frame_with_portrait_requested_size(self):
        # Run34775850505 relaunch retained a portrait request while the actual
        # gateway screenshot and display were landscape. Frames is AOSP's -a
        # layout field, not a transformed screenshot or requested-size fallback.
        self.assertTrue(gate.input_window_ready(READY.replace('Requested w=1280 h=720','Requested w=720 h=1280',1)))

    def test_frame_dimensions_use_extents_and_reject_empty_or_inverted(self):
        self.assertTrue(gate.input_window_ready(READY.replace('frame=[0,0][1280,720]','frame=[40,24][1240,696]',1)))
        for bounds in ('[0,0][0,0]', '[0,720][1280,0]', '[1280,0][0,720]'):
            self.assertFalse(gate.input_window_ready(READY.replace('frame=[0,0][1280,720]','frame='+bounds,1)))

    def test_focused_window_cannot_borrow_another_window_frame(self):
        self.assertFalse(gate.input_window_ready(READY.replace(' frame=[0,0][1280,720]','',1)))
        self.assertFalse(gate.input_window_ready(READY.replace('mHaveFrame=true','mHaveFrame=false',1)))

    def test_other_focus(self):
        self.assertFalse(gate.input_window_ready(READY.replace('mCurrentFocus='+APP,'mCurrentFocus=Window{other u0 com.android.launcher/Home}')))

    def test_unready_app_cannot_borrow_other_window_surface(self):
        self.assertFalse(gate.input_window_ready(READY.replace('mHasSurface=true','mHasSurface=false',1)))
        self.assertFalse(gate.input_window_ready(READY.replace('isVisible=true','isVisible=false',1)))
        self.assertFalse(gate.input_window_ready(READY.replace('Surface: shown=true','Surface: shown=false',1)))

    def test_rotation_or_portrait(self):
        self.assertFalse(gate.input_window_ready(READY.replace('no ScreenRotationAnimation','ScreenRotationAnimation running')))
        self.assertFalse(gate.input_window_ready(READY.replace('frame=[0,0][1280,720]','frame=[0,0][720,1280]',1)))

    def test_missing_fields_fail_closed(self):
        for text in ('', 'mCurrentFocus='+APP, READY.replace(' frame=[0,0][1280,720]','',1), READY.replace('mHaveFrame=true','',1)):
            self.assertFalse(gate.input_window_ready(text))

    def test_focus_loss_restarts_stabilization_and_retains_dump(self):
        clock=[0.0]
        frames=iter([READY,READY,'',READY,READY,READY,READY])
        with tempfile.TemporaryDirectory() as directory, patch.object(gate,'OUT',Path(directory)), patch.object(gate,'adb',lambda *_:next(frames)), patch.object(gate.time,'monotonic',lambda:clock[0]), patch.object(gate.time,'sleep',lambda _:clock.__setitem__(0,clock[0]+1)):
            gate.wait_for_input_ready()
            self.assertEqual(clock[0],6)
            self.assertEqual((Path(directory)/'resume-window-state.txt').read_text(),READY)

    def test_never_ready_times_out_without_injecting_input(self):
        clock=[0.0]
        calls=[]
        def adb(*args):
            calls.append(args)
            return ''
        with tempfile.TemporaryDirectory() as directory, patch.object(gate,'OUT',Path(directory)), patch.object(gate,'adb',adb), patch.object(gate.time,'monotonic',lambda:clock[0]), patch.object(gate.time,'sleep',lambda _:clock.__setitem__(0,clock[0]+1)):
            with self.assertRaises(AssertionError):gate.wait_for_input_ready()
        self.assertTrue(all(args==('shell','dumpsys','window','-a') for args in calls))

if __name__=='__main__':
    unittest.main()
