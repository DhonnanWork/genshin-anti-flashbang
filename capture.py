import numpy as np
from window_utils import get_window_rect

def get_window_brightness(hwnd, sct):
    try:
        left, top, width, height = get_window_rect(hwnd)
        if width <= 10 or height <= 10:
            return 0.0
            
        cw = width // 4
        ch = height // 2
        box = 10
        gray_sum = 0.0
        
        for row in range(2):
            for col in range(4):
                cx = left + col * cw + cw // 2
                cy = top + row * ch + ch // 2
                
                monitor = {
                    "left": cx - box // 2,
                    "top": cy - box // 2,
                    "width": box,
                    "height": box
                }
                img = sct.grab(monitor)
                frame = np.array(img, copy=False)
                gray = np.dot(frame[..., :3], [0.114, 0.587, 0.299])
                gray_sum += np.mean(gray)
                
        return (gray_sum / 8.0) / 255.0
    except Exception:
        return 0.0

def get_border_brightness(hwnd, sct):
    try:
        left, top, width, height = get_window_rect(hwnd)
        if width <= 12 or height <= 12:
            return 0.0
            
        offset = 5
        strips =[
            {"left": left, "top": top + offset, "width": width, "height": 1},
            {"left": left, "top": top + height - 1 - offset, "width": width, "height": 1},
            {"left": left + offset, "top": top, "width": 1, "height": height},
            {"left": left + width - 1 - offset, "top": top, "width": 1, "height": height}
        ]
        
        gray_sum = 0.0
        for mon in strips:
            img = sct.grab(mon)
            frame = np.array(img, copy=False)
            gray = np.dot(frame[..., :3], [0.114, 0.587, 0.299])
            gray_sum += np.mean(gray)
            
        return (gray_sum / 4.0) / 255.0
    except Exception:
        return 0.0