import time
import win32gui
import win32con
import pythoncom
from mss import MSS
from window_utils import get_window_rect
from capture import get_border_brightness
from config import BRIGHTNESS_THRESHOLD

class FadeOverlay:
    _class_registered = False
    _class_name = "FadeOverlayClass"

    def __init__(self, target_hwnd):
        self.target_hwnd = target_hwnd
        self.hwnd = None
        self.running = False
        self._register_class()

    def _register_class(self):
        if not FadeOverlay._class_registered:
            wc = win32gui.WNDCLASS()
            wc.lpszClassName = FadeOverlay._class_name
            wc.hbrBackground = win32gui.GetStockObject(win32con.BLACK_BRUSH)
            wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
            wc.lpfnWndProc = win32gui.DefWindowProc
            try:
                win32gui.RegisterClass(wc)
                FadeOverlay._class_registered = True
            except Exception:
                pass

    def _update_position(self):
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            return
        try:
            left, top, width, height = get_window_rect(self.target_hwnd)
            if width > 2 and height > 2:
                win32gui.SetWindowPos(
                    self.hwnd, win32con.HWND_TOPMOST, 
                    left + 1, top + 1, width - 2, height - 2, 
                    win32con.SWP_NOACTIVATE
                )
        except Exception:
            pass

    def show_with_fade(self, solid_duration=2.0, fade_duration=2.0):
        self.running = True
        pythoncom.CoInitialize()
        local_sct = MSS()
        
        self.hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW,
            FadeOverlay._class_name,
            "FadeOverlay",
            win32con.WS_POPUP,
            0, 0, 100, 100,
            None, None, None, None
        )
        
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 255, win32con.LWA_ALPHA)
        self._update_position()
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOWNOACTIVATE)

        verification_failed = False
        for _ in range(10):
            if not self.running:
                break
            time.sleep(0.1)
            win32gui.PumpWaitingMessages()
            self._update_position()
            
            border_brightness = get_border_brightness(self.target_hwnd, local_sct)
            if border_brightness < BRIGHTNESS_THRESHOLD:
                verification_failed = True
                print("False positive detected. Aborting overlay.")
                break

        if verification_failed or not self.running:
            if self.hwnd and win32gui.IsWindow(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
                win32gui.DestroyWindow(self.hwnd)
            self.hwnd = None
            self.running = False
            local_sct.close()
            pythoncom.CoUninitialize()
            return

        remaining_solid = max(0.0, solid_duration - 1.0)
        if remaining_solid > 0:
            time.sleep(remaining_solid)

        while self.running:
            win32gui.PumpWaitingMessages()
            self._update_position()
            
            border_brightness = get_border_brightness(self.target_hwnd, local_sct)
            if border_brightness < BRIGHTNESS_THRESHOLD:
                break
                
            time.sleep(0.05)

        steps = int(fade_duration / 0.03)
        for i in range(steps):
            if not self.running:
                break
            opacity = 255 - int((i / steps) * 255)
            try:
                win32gui.SetLayeredWindowAttributes(self.hwnd, 0, opacity, win32con.LWA_ALPHA)
            except Exception:
                pass
            win32gui.PumpWaitingMessages()
            self._update_position()
            time.sleep(0.03)

        if self.hwnd and win32gui.IsWindow(self.hwnd):
            win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
            win32gui.DestroyWindow(self.hwnd)
            
        self.hwnd = None
        self.running = False
        local_sct.close()
        pythoncom.CoUninitialize()

    def destroy(self):
        self.running = False