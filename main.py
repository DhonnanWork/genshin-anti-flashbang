import time
import threading
import ctypes
import atexit
from mss import MSS

from config import CHECK_INTERVAL_MS, BRIGHTNESS_THRESHOLD
from window_utils import get_target_window
from capture import get_window_brightness, get_border_brightness
from overlay import FadeOverlay

winmm = ctypes.windll.winmm
winmm.timeBeginPeriod(1)
atexit.register(lambda: winmm.timeEndPeriod(1))

def main():
    hwnd, title = get_target_window()
    if not hwnd:
        print("No window selected. Exiting.")
        return

    print(f"\nMonitoring window: {title}")
    
    overlay = FadeOverlay(hwnd)
    sct = MSS()

    print(f"Checking brightness every {CHECK_INTERVAL_MS} ms. Press Ctrl+C to stop.\n")
    try:
        while True:
            start = time.perf_counter()
            brightness = get_window_brightness(hwnd, sct)
            
            if brightness > BRIGHTNESS_THRESHOLD:
                border_brightness = get_border_brightness(hwnd, sct)
                if border_brightness > BRIGHTNESS_THRESHOLD:
                    if not overlay.running:
                        print(f"Trigger! Center = {brightness:.2f}, Border = {border_brightness:.2f}")
                        threading.Thread(target=overlay.show_with_fade, args=(2.0, 2.0), daemon=True).start()
                        time.sleep(1.0)
                
            elapsed = (time.perf_counter() - start) * 1000
            sleep_ms = max(0, CHECK_INTERVAL_MS - elapsed)
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        overlay.destroy()
        sct.close()

if __name__ == "__main__":
    main()