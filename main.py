import time
import threading
import ctypes
import atexit
import win32gui
from mss import MSS

from config import CHECK_INTERVAL_MS, BRIGHTNESS_THRESHOLD, SOLID_DURATION, FADE_DURATION
from window_utils import get_target_window
from capture import get_window_brightness, get_border_brightness
from overlay import FadeOverlay

def initialize_system_timer() -> None:
    winmm = ctypes.windll.winmm
    assert winmm is not None
    winmm.timeBeginPeriod(1)
    atexit.register(lambda: winmm.timeEndPeriod(1))

def check_and_trigger_overlay(hwnd: int, sct: MSS, overlay: FadeOverlay) -> bool:
    assert isinstance(hwnd, int)
    assert sct is not None
    assert overlay is not None
    
    brightness = get_window_brightness(hwnd, sct)
    assert 0.0 <= brightness <= 1.0
    
    if brightness > BRIGHTNESS_THRESHOLD:
        border_brightness = get_border_brightness(hwnd, sct)
        assert 0.0 <= border_brightness <= 1.0
        
        if border_brightness > BRIGHTNESS_THRESHOLD:
            if not overlay.running:
                print(f"Trigger! Center = {brightness:.2f}, Border = {border_brightness:.2f}")
                
                overlay_thread = threading.Thread(
                    target=overlay.show_with_fade, 
                    args=(SOLID_DURATION, FADE_DURATION), 
                    daemon=True
                )
                overlay_thread.start()
                time.sleep(0.5)
                return True
    return False

def wait_for_overlay_and_cooldown(hwnd: int, sct: MSS, overlay: FadeOverlay) -> None:
    assert isinstance(hwnd, int)
    assert sct is not None
    assert overlay is not None
    
    max_safety_wait_loops = 500
    
    for _ in range(max_safety_wait_loops):
        is_window_active = win32gui.IsWindow(hwnd)
        if not is_window_active or not overlay.running:
            break
        time.sleep(0.1)
        
    for _ in range(max_safety_wait_loops):
        is_window_active = win32gui.IsWindow(hwnd)
        if not is_window_active:
            break
        brightness = get_window_brightness(hwnd, sct)
        if brightness < BRIGHTNESS_THRESHOLD:
            break
        time.sleep(0.1)

def run_monitoring_loop(hwnd: int, sct: MSS, overlay: FadeOverlay) -> None:
    assert isinstance(hwnd, int)
    assert sct is not None
    assert overlay is not None
    
    max_statically_bounded_runs = 1_000_000_000
    
    for _ in range(max_statically_bounded_runs):
        is_window_active = win32gui.IsWindow(hwnd)
        if not is_window_active:
            print("Target window closed. Exiting.")
            break
            
        start_time = time.perf_counter()
        did_trigger = check_and_trigger_overlay(hwnd, sct, overlay)
        assert isinstance(did_trigger, bool)
        
        if did_trigger:
            wait_for_overlay_and_cooldown(hwnd, sct, overlay)
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        sleep_duration_ms = max(0.0, CHECK_INTERVAL_MS - elapsed_ms)
        time.sleep(sleep_duration_ms / 1000.0)

def main() -> None:
    initialize_system_timer()
    hwnd, title = get_target_window()
    
    if hwnd is None:
        print("No window selected. Exiting.")
        return
        
    assert isinstance(hwnd, int)
    print(f"\nMonitoring window: {title}")
    
    overlay = FadeOverlay(hwnd)
    sct = MSS()
    
    try:
        run_monitoring_loop(hwnd, sct, overlay)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        overlay.destroy()
        sct.close()

if __name__ == "__main__":
    main()