import numpy as np
from window_utils import get_window_rect

def get_window_brightness(hwnd, sct):
    try:
        left, top, width, height = get_window_rect(hwnd)
        if width <= 10 or height <= 10:
            return 0.0

        # -> OPTIMIZATION 1: Take exactly ONE screen grab of the entire window area
        monitor = {
            "left": left,
            "top": top,
            "width": width,
            "height": height
        }
        img = sct.grab(monitor)
        frame = np.array(img, copy=False)  # Fast, zero-copy view of BGRA data

        cw = width // 4
        ch = height // 2
        box = 10
        gray_sum = 0.0

        for row in range(2):
            for col in range(4):
                # Calculate center positions relative to the captured frame (0,0 is top-left)
                local_cx = col * cw + cw // 2
                local_cy = row * ch + ch // 2

                # Define bounds safely inside the frame limits
                y_start = max(0, local_cy - box // 2)
                y_end = min(height, y_start + box)
                x_start = max(0, local_cx - box // 2)
                x_end = min(width, x_start + box)

                # -> OPTIMIZATION 2: Extract the small box via rapid memory slicing
                box_slice = frame[y_start:y_end, x_start:x_end]
                
                # Convert only this tiny 10x10 slice to grayscale (B, G, R weighting)
                gray = np.dot(box_slice[..., :3], [0.114, 0.587, 0.299])
                gray_sum += np.mean(gray)

        return (gray_sum / 8.0) / 255.0
    except Exception:
        return 0.0

def get_border_brightness(hwnd, sct):
    try:
        left, top, width, height = get_window_rect(hwnd)
        if width <= 12 or height <= 12:
            return 0.0

        # -> OPTIMIZATION 1: Take exactly ONE screen grab of the entire window area
        monitor = {
            "left": left,
            "top": top,
            "width": width,
            "height": height
        }
        img = sct.grab(monitor)
        frame = np.array(img, copy=False)

        offset = 5
        
        # -> OPTIMIZATION 2: Pull 1-pixel wide strips directly from the array using NumPy indexing
        # Top and bottom strips (rows)
        top_strip = frame[offset, :, :3]
        bottom_strip = frame[height - 1 - offset, :, :3]
        
        # Left and right strips (columns)
        left_strip = frame[:, offset, :3]
        right_strip = frame[:, width - 1 - offset, :3]

        # Calculate brightness on each index strip instantly
        gray_sum = (
            np.mean(np.dot(top_strip, [0.114, 0.587, 0.299])) +
            np.mean(np.dot(bottom_strip, [0.114, 0.587, 0.299])) +
            np.mean(np.dot(left_strip, [0.114, 0.587, 0.299])) +
            np.mean(np.dot(right_strip, [0.114, 0.587, 0.299]))
        )

        return (gray_sum / 4.0) / 255.0
    except Exception:
        return 0.0