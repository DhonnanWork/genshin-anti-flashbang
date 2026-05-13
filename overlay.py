import time
import win32gui
import win32api
import win32con
import pythoncom
from mss import MSS
from window_utils import get_window_rect
from capture import get_border_brightness
from input_check import is_any_button_pressed
from config import BRIGHTNESS_THRESHOLD, ENABLE_CANCEL_BUTTON, FALSE_POSITIVE_CHECK_SEC

class FadeOverlay:
    _class_registered = False
    _class_name = "FadeOverlayClass"

    def __init__(self, target_hwnd):
        self.target_hwnd = target_hwnd
        self.hwnd = None
        self.running = False
        self._register_class()

    def on_destroy(self, hwnd, msg, wparam, lparam):
        win32gui.PostQuitMessage(0)
        return 0

    def _register_class(self):
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

    def _update_position(self):
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            return
        try:
            left, top, width, height = get_window_rect(self.target_hwnd)
            inset = 6 
            
            if width > (inset * 2) and height > (inset * 2):
                win32gui.SetWindowPos(
                    self.hwnd, win32con.HWND_TOPMOST, 
                    left + inset, top + inset, width - (inset * 2), height - (inset * 2), 
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

        start_time = time.perf_counter()
        is_false_positive = False
        was_canceled = False
        
        time.sleep(0.3)
        
        while self.running:
            win32gui.PumpWaitingMessages()
            self._update_position()
            
            if ENABLE_CANCEL_BUTTON and is_any_button_pressed():
                was_canceled = True
                print("Cancel button detected. Aborting overlay.")
                break
                
            elapsed = time.perf_counter() - start_time
            border_brightness = get_border_brightness(self.target_hwnd, local_sct)
            
            if border_brightness < BRIGHTNESS_THRESHOLD:
                if elapsed < FALSE_POSITIVE_CHECK_SEC:
                    is_false_positive = True
                    print("False positive (flash) detected. Aborting overlay.")
                break
                
            time.sleep(0.05)

        if was_canceled or is_false_positive or not self.running:
            if self.hwnd and win32gui.IsWindow(self.hwnd):
                win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)
                win32gui.DestroyWindow(self.hwnd)
            self.hwnd = None
            self.running = False
            local_sct.close()
            pythoncom.CoUninitialize()
            return

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