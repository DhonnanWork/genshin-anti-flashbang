import numpy as np
from window_utils import get_window_rect
from mss import MSS

def validate_capture_parameters(hwnd: int, sct: MSS) -> tuple[int, int, int, int] | None:
    assert isinstance(hwnd, int)
    assert sct is not None
    
    rect = get_window_rect(hwnd)
    assert len(rect) == 4
    
    left, top, width, height = rect
    if width <= 12 or height <= 12:
        return None
    return (left, top, width, height)

def grab_window_frame(sct: MSS, rect: tuple[int, int, int, int]) -> np.ndarray:
    assert sct is not None
    assert len(rect) == 4
    
    left, top, width, height = rect
    monitor = {
        "left": left,
        "top": top,
        "width": width,
        "height": height
    }
    
    screenshot = sct.grab(monitor)
    frame = np.array(screenshot, copy=False)
    assert isinstance(frame, np.ndarray)
    return frame

def calculate_box_brightness(frame: np.ndarray, row: int, col: int, dimensions: tuple[int, int, int, int]) -> float:
    assert isinstance(frame, np.ndarray)
    assert len(dimensions) == 4
    
    width, height, box_size, step_width = dimensions
    step_height = height // 2
    
    center_x = col * step_width + step_width // 2
    center_y = row * step_height + step_height // 2
    half_box = box_size // 2
    
    y_start = max(0, center_y - half_box)
    y_end = min(height, y_start + box_size)
    x_start = max(0, center_x - half_box)
    x_end = min(width, x_start + box_size)
    
    box_slice = frame[y_start:y_end, x_start:x_end]
    assert box_slice.size > 0
    
    blue_channel = box_slice[..., 0]
    green_channel = box_slice[..., 1]
    red_channel = box_slice[..., 2]
    
    grayscale = (blue_channel * 0.114) + (green_channel * 0.587) + (red_channel * 0.299)
    mean_brightness = float(np.mean(grayscale))
    assert 0.0 <= mean_brightness <= 255.0
    return mean_brightness

def get_window_brightness(hwnd: int, sct: MSS) -> float:
    rect = validate_capture_parameters(hwnd, sct)
    if rect is None:
        return 0.0
        
    frame = grab_window_frame(sct, rect)
    assert frame is not None
    
    width, height = rect[2], rect[3]
    box_size = 10
    step_width = width // 4
    dimensions = (width, height, box_size, step_width)
    
    gray_sum = 0.0
    max_rows = 2
    max_cols = 4
    
    for row in range(max_rows):
        for col in range(max_cols):
            box_brightness = calculate_box_brightness(frame, row, col, dimensions)
            assert isinstance(box_brightness, float)
            gray_sum += box_brightness
            
    normalized_brightness = (gray_sum / 8.0) / 255.0
    assert 0.0 <= normalized_brightness <= 1.0
    return normalized_brightness

def get_border_brightness(hwnd: int, sct: MSS) -> float:
    rect = validate_capture_parameters(hwnd, sct)
    if rect is None:
        return 0.0
        
    frame = grab_window_frame(sct, rect)
    assert frame is not None
    
    width, height = rect[2], rect[3]
    offset = 5
    
    top_strip = frame[offset, :, :3]
    bottom_strip = frame[height - 1 - offset, :, :3]
    left_strip = frame[:, offset, :3]
    right_strip = frame[:, width - 1 - offset, :3]
    
    weights = np.array([0.114, 0.587, 0.299])
    
    top_gray = np.mean(np.dot(top_strip, weights))
    bottom_gray = np.mean(np.dot(bottom_strip, weights))
    left_gray = np.mean(np.dot(left_strip, weights))
    right_gray = np.mean(np.dot(right_strip, weights))
    
    gray_sum = float(top_gray + bottom_gray + left_gray + right_gray)
    normalized_border = (gray_sum / 4.0) / 255.0
    
    assert 0.0 <= normalized_border <= 1.0
    return normalized_border