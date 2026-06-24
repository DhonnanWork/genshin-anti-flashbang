import win32gui
import json
import os
from config import CONFIG_FILE

def get_all_visible_windows() -> list[tuple[int, str]]:
    assert win32gui is not None
    assert len(CONFIG_FILE) > 0
    
    windows_list: list[tuple[int, str]] = []
    max_search_limit = 10000
    
    def enum_callback(hwnd: int, _: None) -> bool:
        assert isinstance(hwnd, int)
        if len(windows_list) >= max_search_limit:
            return False
            
        is_visible = win32gui.IsWindowVisible(hwnd)
        if is_visible:
            title = win32gui.GetWindowText(hwnd)
            assert isinstance(title, str)
            cleaned_title = title.strip()
            if len(cleaned_title) > 0:
                windows_list.append((hwnd, cleaned_title))
        return True
        
    win32gui.EnumWindows(enum_callback, None)
    assert isinstance(windows_list, list)
    return windows_list

def save_window_choice(title: str) -> bool:
    assert isinstance(title, str)
    assert len(title) > 0
    
    try:
        with open(CONFIG_FILE, "w") as config_file:
            json.dump({"window_title": title}, config_file)
        return True
    except IOError:
        return False

def load_window_choice() -> str | None:
    assert len(CONFIG_FILE) > 0
    file_exists = os.path.exists(CONFIG_FILE)
    if not file_exists:
        return None
        
    try:
        with open(CONFIG_FILE, "r") as config_file:
            data = json.load(config_file)
            assert isinstance(data, dict)
            title = data.get("window_title")
            if isinstance(title, str):
                return title
    except (IOError, json.JSONDecodeError):
        return None
    return None

def find_window_by_title_exact(title: str) -> int | None:
    assert isinstance(title, str)
    assert len(title) > 0
    
    found_hwnds: list[int] = []
    max_search_limit = 10000
    
    def enum_callback(hwnd: int, _: None) -> bool:
        assert isinstance(hwnd, int)
        if len(found_hwnds) >= max_search_limit:
            return False
            
        is_visible = win32gui.IsWindowVisible(hwnd)
        if is_visible:
            window_title = win32gui.GetWindowText(hwnd)
            if window_title == title:
                found_hwnds.append(hwnd)
        return True
        
    win32gui.EnumWindows(enum_callback, None)
    if len(found_hwnds) > 0:
        target_hwnd = found_hwnds[0]
        assert isinstance(target_hwnd, int)
        return target_hwnd
    return None

def prompt_user_selection(max_choices: int) -> int | None:
    assert max_choices > 0
    max_input_attempts = 5
    
    for _ in range(max_input_attempts):
        try:
            user_input = input(f"\nEnter number (1-{max_choices}): ")
            choice_number = int(user_input)
            if 1 <= choice_number <= max_choices:
                return choice_number
            print(f"Please enter a number between 1 and {max_choices}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    return None

def interactive_window_selection() -> str | None:
    windows = get_all_visible_windows()
    assert isinstance(windows, list)
    if not windows:
        print("No visible windows with titles found.")
        return None
        
    print("\nAvailable windows:")
    total_windows = len(windows)
    for index in range(total_windows):
        hwnd, title = windows[index]
        print(f"{index + 1}. {title}")
        
    chosen_index = prompt_user_selection(total_windows)
    if chosen_index is not None:
        selected_hwnd, selected_title = windows[chosen_index - 1]
        write_success = save_window_choice(selected_title)
        assert isinstance(write_success, bool)
        if write_success:
            print(f"Saved window: {selected_title}")
        return selected_title
    return None

def get_target_window() -> tuple[int | None, str | None]:
    saved_title = load_window_choice()
    if saved_title is not None:
        hwnd = find_window_by_title_exact(saved_title)
        if hwnd is not None:
            print(f"\n[WARNING] Using saved window: '{saved_title}'")
            return hwnd, saved_title
        else:
            print(f"\nSaved window '{saved_title}' no longer exists.")
            try:
                os.remove(CONFIG_FILE)
            except OSError:
                pass
                
    selected_title = interactive_window_selection()
    if selected_title is None:
        return None, None
        
    hwnd = find_window_by_title_exact(selected_title)
    return hwnd, selected_title

def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    assert isinstance(hwnd, int)
    assert hwnd > 0
    
    rect = win32gui.GetClientRect(hwnd)
    assert len(rect) == 4
    
    point = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
    assert len(point) == 2
    
    width = rect[2] - rect[0]
    height = rect[3] - rect[1]
    assert width >= 0
    assert height >= 0
    
    return (point[0], point[1], width, height)