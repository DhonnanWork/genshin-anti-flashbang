import win32gui
import json
import os
from config import CONFIG_FILE

def get_all_visible_windows():
    windows =[]
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title.strip():
                windows.append((hwnd, title))
        return True
    win32gui.EnumWindows(enum_callback, None)
    return windows

def save_window_choice(title):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"window_title": title}, f)

def load_window_choice():
    if not os.path.exists(CONFIG_FILE):
        return None
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        return data.get("window_title")

def find_window_by_title_exact(title):
    def enum_callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) == title:
            hwnd_list.append(hwnd)
        return True
    hwnd_list =[]
    win32gui.EnumWindows(enum_callback, hwnd_list)
    return hwnd_list[0] if hwnd_list else None

def interactive_window_selection():
    print("\nScanning for visible windows...")
    windows = get_all_visible_windows()
    if not windows:
        print("No visible windows with titles found.")
        return None
    print("\nAvailable windows:")
    for idx, (hwnd, title) in enumerate(windows):
        print(f"{idx+1}. {title}")
    while True:
        try:
            choice = int(input(f"\nEnter number (1-{len(windows)}): "))
            if 1 <= choice <= len(windows):
                selected_title = windows[choice-1][1]
                save_window_choice(selected_title)
                print(f"Saved window: {selected_title}")
                return selected_title
            else:
                print(f"Please enter a number between 1 and {len(windows)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_target_window():
    saved_title = load_window_choice()
    if saved_title:
        hwnd = find_window_by_title_exact(saved_title)
        if hwnd:
            print(f"\n[WARNING] Using saved window: '{saved_title}'")
            print(f"          Delete '{CONFIG_FILE}' to change the window.")
            return hwnd, saved_title
        else:
            print(f"\nSaved window '{saved_title}' no longer exists. Running interactive selection.")
            os.remove(CONFIG_FILE)
    title = interactive_window_selection()
    if not title:
        return None, None
    hwnd = find_window_by_title_exact(title)
    return hwnd, title

def get_window_rect(hwnd):
    rect = win32gui.GetClientRect(hwnd)
    point = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
    return (point[0], point[1], rect[2] - rect[0], rect[3] - rect[1])