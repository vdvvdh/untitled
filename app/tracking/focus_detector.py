"""
Foreground window detection.
Tells us which process currently has focus (is the active window).
"""

import psutil
import win32gui
import win32process


def get_foreground_process_name() -> str | None:
    """Return the executable name of the currently focused window, or None."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None

    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


if __name__ == "__main__":
    import time

    print("Printing the focused window's process every 2 seconds... (Ctrl+C to stop)")
    try:
        while True:
            print(get_foreground_process_name())
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopped.")