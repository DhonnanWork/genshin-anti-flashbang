import ctypes
import subprocess
import sys
import time
from pathlib import Path

TARGET_WINDOW = "Genshin Impact"
MAIN_SCRIPT = Path(__file__).parent / "main.py"

def find_window_by_title(title):
    """Return window handle (HWND) if a window with exact title exists."""
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, title)
    return hwnd if hwnd != 0 else None

def run_main_script():
    """Execute main.py and wait for it to complete."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Window '{TARGET_WINDOW}' found! Starting {MAIN_SCRIPT.name}...")
    # This blocks the checker script until main.py exits
    subprocess.run([sys.executable, str(MAIN_SCRIPT)], check=False)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {MAIN_SCRIPT.name} has stopped. Resuming search...")

def main():
    # Enforce single instance using a system-wide Named Mutex
    kernel32 = ctypes.windll.kernel32
    mutex_name = "Local\\GenshinBrightnessOverlayMonitorMutex"
    
    # CreateMutexW arguments: lpMutexAttributes, bInitialOwner, lpName
    mutex = kernel32.CreateMutexW(None, True, mutex_name)
    last_error = kernel32.GetLastError()
    
    # 183 corresponds to ERROR_ALREADY_EXISTS
    if last_error == 183:
        print("Another instance of the Genshin Window Checker is already running. Exiting.")
        sys.exit(0)

    print(f"Genshin Window Checker started. Monitoring for '{TARGET_WINDOW}'...")
    print("Keep this window open, or run it in the background.")
    
    try:
        while True:
            hwnd = find_window_by_title(TARGET_WINDOW)
            if hwnd:
                run_main_script()
            
            # Check if the game is opened every 3 seconds
            time.sleep(3)
    except KeyboardInterrupt:
        print("\nExiting monitor.")
    finally:
        if mutex:
            kernel32.ReleaseMutex(mutex)
            kernel32.CloseHandle(mutex)

if __name__ == "__main__":
    main()