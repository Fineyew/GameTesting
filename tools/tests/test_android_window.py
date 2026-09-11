"""API35 resume readiness regression using the retained run34548765608 dump shape."""
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
    mHasSurface=true isReadyForDisplay()=true mWindowRemovalAllowed=false
      Surface: shown=true    mForceSeamlesslyRotate=false seamlesslyRotate: pending=null
    isVisible=true
  Window #8 Window{{other u0 com.android.launcher/Home}}:
    Requested w=1280 h=720
    mHasSurface=true isReadyForDisplay()=true
      Surface: shown=true
    isVisible=true
'''

class AndroidWindowTests(unittest.TestCase):
    def test_actual_api35_shape_without_legacy_transition_field(self):
        self.assertTrue(gate.input_window_ready(READY))

    def test_other_focus(self):
        self.assertFalse(gate.input_window_ready(READY.replace('mCurrentFocus='+APP,'mCurrentFocus=Window{other u0 com.android.launcher/Home}')))

    def test_unready_app_cannot_borrow_other_window_surface(self):
        self.assertFalse(gate.input_window_ready(READY.replace('mHasSurface=true','mHasSurface=false',1)))
        self.assertFalse(gate.input_window_ready(READY.replace('isVisible=true','isVisible=false',1)))
        self.assertFalse(gate.input_window_ready(READY.replace('Surface: shown=true','Surface: shown=false',1)))

    def test_rotation_or_portrait(self):
        self.assertFalse(gate.input_window_ready(READY.replace('no ScreenRotationAnimation','ScreenRotationAnimation running')))
        self.assertFalse(gate.input_window_ready(READY.replace('Requested w=1280 h=720','Requested w=720 h=1280',1)))

    def test_missing_fields_fail_closed(self):
        for text in ('', 'mCurrentFocus='+APP, READY.replace('Requested w=1280 h=720','',1)):
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
        self.assertTrue(all(args==('shell','dumpsys','window') for args in calls))

if __name__=='__main__':
    unittest.main()
