import win32api
import win32con
import win32gui
import ctypes
from ctypes import wintypes
import time

WINDOW_TITLE = "Rucoy Online"

KEY_BINDINGS = {
    "1": (90, 606), 
    "2": (90, 790), 
    "3": (86, 968), 
    "F": (1827, 426), 
    "E": (1861, 75), 
    "C": (1298, 75), 
    "M": (1404, 80), 
    "T": (1521, 76), 
    "Q": (77, 431)
}

# Global window handle for the target window
hwnd = win32gui.FindWindowEx(None, None, None, WINDOW_TITLE)

def c(x, y, delay=0.1):
    """
    Simulates a click at the given (x, y) coordinates on the target window.
    """
    global hwnd
    screen_x, screen_y = win32gui.ClientToScreen(hwnd, (x, y))
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, screen_y * 0x10000 + screen_x)
    win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, screen_y * 0x10000 + screen_x)
    time.sleep(delay)

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]

def get_foreground_window_title():
    """
    Returns the title of the currently active (foreground) window.
    """
    fg_hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(fg_hwnd)

# Dictionary to track the state of keys (pressed or released)
key_states = {}

def low_level_keyboard_proc(nCode, wParam, lParam):
    if nCode == 0:  # HC_ACTION
        kbd_struct = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk_code = kbd_struct.vkCode
        key = chr(vk_code)

        # Check if the active window is the target window
        if get_foreground_window_title() == WINDOW_TITLE:
            # Handle key press (WM_KEYDOWN) and release (WM_KEYUP)
            if wParam == WM_KEYDOWN:
                if key in KEY_BINDINGS and not key_states.get(key, False):
                    x, y = KEY_BINDINGS[key]
                    c(x, y)  # Trigger the click function
                    key_states[key] = True  # Mark the key as pressed
                    return 1  # Block the key press
            elif wParam == 0x0101:  # WM_KEYUP
                if key in KEY_BINDINGS:
                    key_states[key] = False  # Mark the key as released

    # Pass the event to the next hook in the chain
    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, ctypes.cast(lParam, ctypes.c_void_p))

def install_keyboard_hook():
    """
    Installs a low-level keyboard hook to intercept input.
    """
    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    hook_proc = HOOKPROC(low_level_keyboard_proc)

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hook = user32.SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc, 0, 0)

    if not hook:
        print("Failed to install keyboard hook.")
        print("Error code:", ctypes.GetLastError())
        return

    print(f"Keyboard hook installed. Listening for keys on '{WINDOW_TITLE}'...")

    # Message loop to keep the hook active
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

    # Unhook when done (unreachable in this case unless interrupted)
    user32.UnhookWindowsHookEx(hook)

if __name__ == "__main__":
    install_keyboard_hook()
