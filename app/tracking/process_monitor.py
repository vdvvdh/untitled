"""
Minimal process monitor experiment.
Polls running processes and detects when a target executable starts/stops.
This is a console-only proof of concept — no UI, no database yet.
"""

import time
import psutil

# Change this to match the process you want to detect.
# For Minecraft Java Edition, the actual game process is usually "javaw.exe",
# but note the launcher also runs as a separate process — we're only
# targeting the game process here, not the launcher.
TARGET_EXECUTABLE = "javaw.exe"

POLL_INTERVAL_SECONDS = 3


def is_target_running(target_name: str) -> bool:
    """Return True if a process with the given executable name is running."""
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == target_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def main():
    print(f"Watching for '{TARGET_EXECUTABLE}'... (Ctrl+C to stop)")
    was_running = False

    while True:
        currently_running = is_target_running(TARGET_EXECUTABLE)

        if currently_running and not was_running:
            print(f"[EVENT] {TARGET_EXECUTABLE} STARTED")
        elif not currently_running and was_running:
            print(f"[EVENT] {TARGET_EXECUTABLE} STOPPED")

        was_running = currently_running
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")