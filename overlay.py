import time
import win32gui
import win32con
import pythoncom
from mss import MSS
from window_utils import get_window_rect
from capture import get_border_brightness
from config import BRIGHTNESS_THRESHOLD, FALSE_POSITIVE_CHECK_SEC

class FadeOverlay:
    _class_registered = False
    _class_name = "FadeOverlayClass"

    def __init__(self, target_hwnd: int):
        assert isinstance(target_hwnd, int)
        assert target_hwnd > 0
        
        self.target_hwnd = target_hwnd
        self.hwnd = None
        self.running = False
        self._register_class()
        
        assert self.target_hwnd == target_hwnd

    def on_destroy(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        assert isinstance(hwnd, int)
        win32gui.PostQuitMessage(0)
        return 0

    def _register_class(self) -> None:
        if not FadeOverlay._class_registered:
            wc = win32gui.WNDCLASS()
            wc.lpszClassName = FadeOverlay._class_name
            wc.hbrBackground = win32gui.GetStockObject(win32con.BLACK_BRUSH)
            wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
            wc.lpfnWndProc = {
                win32con.WM_DESTROY: self.on_destroy
            }
            try:
                win32gui.RegisterClass(wc)
                FadeOverlay._class_registered = True
            except Exception:
                pass
        assert FadeOverlay._class_registered is True

    def _update_position(self) -> None:
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            return
            
        rect = get_window_rect(self.target_hwnd)
        assert len(rect) == 4
        left, top, width, height = rect
        
        inset = 6
        if width > (inset * 2) and height > (inset * 2):
            win32gui.SetWindowPos(
                self.hwnd, win32con.HWND_TOPMOST, 
                left + inset, top + inset, width - (inset * 2), height - (inset * 2), 
                win32con.SWP_NOACTIVATE
            )

    def _create_overlay_window(self) -> int:
        hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
            FadeOverlay._class_name,
            "FadeOverlay",
            win32con.WS_POPUP,
            0, 0, 100, 100,
            None, None, None, None
        )
        assert hwnd != 0
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
        return hwnd

    def _check_flash_state(self, local_sct: MSS, start_time: float) -> bool:
        assert local_sct is not None
        assert start_time > 0.0
        
        is_false_positive = False
        max_safety_loops = 500
        check_interval = 0.010
        
        for _ in range(max_safety_loops):
            if not self.running:
                break
                
            win32gui.PumpWaitingMessages()
            self._update_position()
            
            elapsed = time.perf_counter() - start_time
            border_brightness = get_border_brightness(self.target_hwnd, local_sct)
            
            if border_brightness < BRIGHTNESS_THRESHOLD:
                if elapsed < FALSE_POSITIVE_CHECK_SEC:
                    is_false_positive = True
                break
                
            time.sleep(check_interval)
            
        return is_false_positive

    def _execute_fade_sequence(self, fade_duration: float) -> None:
        assert fade_duration >= 0.0
        
        max_fade_steps_limit = 500
        step_duration = 0.03
        calculated_steps = int(fade_duration / step_duration)
        steps = min(max_fade_steps_limit, max(1, calculated_steps))
        
        for step in range(steps):
            if not self.running:
                break
                
            opacity = 255 - int((step / steps) * 255)
            try:
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, opacity, win32con.LWA_ALPHA)
            except Exception:
                pass
                
            win32gui.PumpWaitingMessages()
            self._update_position()
            time.sleep(step_duration)

    def _clean_up_resources(self, local_sct: MSS) -> None:
        assert local_sct is not None
        
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            win32gui.DestroyWindow(self.hwnd)
            
        self.hwnd = None
        self.running = False
        local_sct.close()
        pythoncom.CoUninitialize()
        
        assert self.hwnd is None
        assert self.running is False

    def show_with_fade(self, solid_duration: float = 2.0, fade_duration: float = 2.0) -> None:
        assert solid_duration >= 0.0
        assert fade_duration >= 0.0
        
        self.running = True
        pythoncom.CoInitialize()
        local_sct = MSS()
        
        self.hwnd = self._create_overlay_window()
        self._update_position()
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)
        
        start_time = time.perf_counter()
        time.sleep(0.01)
        
        is_false_positive = self._check_flash_state(local_sct, start_time)
        assert isinstance(is_false_positive, bool)
        
        if not is_false_positive and self.running:
            self._execute_fade_sequence(fade_duration)
            
        self._clean_up_resources(local_sct)

    def destroy(self) -> None:
        self.running = False
        assert self.running is False