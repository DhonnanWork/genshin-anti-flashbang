import time
import threading
import ctypes
import atexit
import win32gui  # Added for window existence checks
from mss import MSS

from config import CHECK_INTERVAL_MS, BRIGHTNESS_THRESHOLD, ENABLE_CANCEL_BUTTON, SOLID_DURATION, FADE_DURATION
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
    
    if ENABLE_CANCEL_BUTTON:
        print(f"-> 'Cancel Overlay by Pressing Any Button' feature is currently ON.")
    else:
        print(f"-> 'Cancel Overlay by Pressing Any Button' feature is currently OFF.")
        print(f"   You can turn it on by changing 'ENABLE_CANCEL_BUTTON = True' in 'config.py'.\n")

    overlay = FadeOverlay(hwnd)
    sct = MSS()

    print(f"Checking brightness every {CHECK_INTERVAL_MS} ms. Press Ctrl+C to stop.\n")
    try:
        while True:
            # Check if Genshin Impact was closed
            if not win32gui.IsWindow(hwnd):
                print("Target window closed. Exiting.")
                break

            start = time.perf_counter()
            brightness = get_window_brightness(hwnd, sct)
            
            if brightness > BRIGHTNESS_THRESHOLD:
                border_brightness = get_border_brightness(hwnd, sct)
                if border_brightness > BRIGHTNESS_THRESHOLD:
                    if not overlay.running:
                        print(f"Trigger! Center = {brightness:.2f}, Border = {border_brightness:.2f}")
                        
                        threading.Thread(target=overlay.show_with_fade, args=(SOLID_DURATION, FADE_DURATION), daemon=True).start()
                        
                        time.sleep(0.5)
                        
                        while overlay.running:
                            if not win32gui.IsWindow(hwnd):
                                break
                            time.sleep(0.1)
                            
                        while win32gui.IsWindow(hwnd) and get_window_brightness(hwnd, sct) >= BRIGHTNESS_THRESHOLD:
                            time.sleep(0.1)
                
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