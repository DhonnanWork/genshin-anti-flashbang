import win32api
import ctypes

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ =[
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", ctypes.c_ulong),
        ("Gamepad", XINPUT_GAMEPAD)
    ]

def is_any_button_pressed():
    for vk in (0x01, 0x02, 0x04, 0x05, 0x06):
        if win32api.GetAsyncKeyState(vk) & 0x8000:
            return True
            
    for vk in range(0x08, 0xFE):
        if win32api.GetAsyncKeyState(vk) & 0x8000:
            return True
            
    try:
        xinput = ctypes.windll.xinput1_4
    except OSError:
        try:
            xinput = ctypes.windll.xinput1_3
        except OSError:
            xinput = None
            
    if xinput:
        state = XINPUT_STATE()
        for i in range(4):
            if xinput.XInputGetState(i, ctypes.byref(state)) == 0:
                if state.Gamepad.wButtons != 0:
                    return True
                if state.Gamepad.bLeftTrigger > 50 or state.Gamepad.bRightTrigger > 50:
                    return True
                    
    return False