"""
Wires together process detection, focus/idle signals, and the state
engine, and persists sessions + segments to SQLite.

This is the orchestrator — the only place that combines everything
from earlier steps into one running loop.
"""

import sqlite3
import time
from datetime import datetime, timezone

from app.database.connection import get_connection
from app.database.migrations import run_migrations
from app.tracking.focus_detector import get_foreground_process_name
from app.tracking.idle_detector import get_idle_seconds
from app.tracking.state_engine import Observation, GameState, classify

TARGET_EXECUTABLE = "javaw.exe"
GAME_NAME = "Minecraft Java Edition"
POLL_INTERVAL_SECONDS = 3


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_target_running(target_name: str) -> bool:
    import psutil
    for proc in psutil.process_iter(attrs=["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == target_name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def get_or_create_game(conn: sqlite3.Connection, name: str, executable_name: str) -> int:
    row = conn.execute(
        "SELECT id FROM games WHERE executable_name = ?", (executable_name,)
    ).fetchone()
    if row:
        return row[0]

    cursor = conn.execute(
        "INSERT INTO games (name, executable_name) VALUES (?, ?)",
        (name, executable_name),
    )
    conn.commit()
    return cursor.lastrowid


def start_session(conn: sqlite3.Connection, game_id: int) -> int:
    cursor = conn.execute(
        "INSERT INTO sessions (game_id, started_at, is_open) VALUES (?, ?, 1)",
        (game_id, now_iso()),
    )
    conn.commit()
    print(f"[SESSION] Started session {cursor.lastrowid}")
    return cursor.lastrowid


def end_session(conn: sqlite3.Connection, session_id: int) -> None:
    conn.execute(
        "UPDATE sessions SET ended_at = ?, is_open = 0 WHERE id = ?",
        (now_iso(), session_id),
    )
    conn.commit()
    print(f"[SESSION] Ended session {session_id}")


def start_segment(conn: sqlite3.Connection, session_id: int, state: GameState) -> int:
    cursor = conn.execute(
        "INSERT INTO session_segments (session_id, state, started_at) VALUES (?, ?, ?)",
        (session_id, state.value, now_iso()),
    )
    conn.commit()
    return cursor.lastrowid


def end_segment(conn: sqlite3.Connection, segment_id: int) -> None:
    conn.execute(
        "UPDATE session_segments SET ended_at = ? WHERE id = ?",
        (now_iso(), segment_id),
    )
    conn.commit()


def main():
    conn = get_connection()
    run_migrations(conn)
    game_id = get_or_create_game(conn, GAME_NAME, TARGET_EXECUTABLE)

    session_id = None
    segment_id = None
    current_state = None

    print(f"Tracking '{TARGET_EXECUTABLE}'... (Ctrl+C to stop)")

    try:
        while True:
            running = is_target_running(TARGET_EXECUTABLE)
            focused = get_foreground_process_name()
            focused_match = bool(focused and focused.lower() == TARGET_EXECUTABLE.lower())
            idle_seconds = get_idle_seconds()

            observation = Observation(
                target_process_running=running,
                target_process_focused=focused_match,
                idle_seconds=idle_seconds,
            )
            new_state = classify(observation)

            # Session boundary: game just started
            if running and session_id is None:
                session_id = start_session(conn, game_id)

            # Session boundary: game just stopped
            if not running and session_id is not None:
                if segment_id is not None:
                    end_segment(conn, segment_id)
                    segment_id = None
                end_session(conn, session_id)
                session_id = None
                current_state = None

            # Segment boundary: state changed while session is open
            if session_id is not None and new_state != current_state:
                if segment_id is not None:
                    end_segment(conn, segment_id)
                segment_id = start_segment(conn, session_id, new_state)
                current_state = new_state
                print(f"[STATE] {new_state.value}")

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\nStopping...")
        if segment_id is not None:
            end_segment(conn, segment_id)
        if session_id is not None:
            end_session(conn, session_id)
        conn.close()
        print("Clean shutdown complete.")


if __name__ == "__main__":
    main()