"""
Idle time detection using Windows' GetLastInputInfo.
Reports how many seconds since the last keyboard/mouse input,
for the interactive session that runs this process.
"""

import ctypes
from ctypes import wintypes


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


def get_idle_seconds() -> float:
    """Return seconds since the last user input in this Windows session."""
    last_input = LASTINPUTINFO()
    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(last_input))

    millis_since_boot = ctypes.windll.kernel32.GetTickCount()
    idle_millis = millis_since_boot - last_input.dwTime

    # Defensive check: input timestamps aren't guaranteed monotonic.
    if idle_millis < 0:
        return 0.0

    return idle_millis / 1000.0


if __name__ == "__main__":
    import time

    print("Printing idle seconds every 2 seconds... (Ctrl+C to stop)")
    try:
        while True:
            print(f"Idle for {get_idle_seconds():.1f}s")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopped.")