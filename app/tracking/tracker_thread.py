"""
Runs the session_manager tracking loop on a background thread,
so the PySide6 UI stays responsive while tracking happens.
"""

from PySide6.QtCore import QThread

from app.database.connection import get_connection
from app.database.migrations import run_migrations
from app.tracking.focus_detector import get_foreground_process_name
from app.tracking.idle_detector import get_idle_seconds
from app.tracking.state_engine import Observation, classify
from app.tracking.session_manager import (
    TARGET_EXECUTABLE,
    GAME_NAME,
    POLL_INTERVAL_SECONDS,
    is_target_running,
    get_or_create_game,
    start_session,
    end_session,
    start_segment,
    end_segment,
)
import time


class TrackerThread(QThread):
    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        conn = get_connection()
        run_migrations(conn)
        game_id = get_or_create_game(conn, GAME_NAME, TARGET_EXECUTABLE)

        session_id = None
        segment_id = None
        current_state = None

        while self._running:
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

            if running and session_id is None:
                session_id = start_session(conn, game_id)

            if not running and session_id is not None:
                if segment_id is not None:
                    end_segment(conn, segment_id)
                    segment_id = None
                end_session(conn, session_id)
                session_id = None
                current_state = None

            if session_id is not None and new_state != current_state:
                if segment_id is not None:
                    end_segment(conn, segment_id)
                segment_id = start_segment(conn, session_id, new_state)
                current_state = new_state

            time.sleep(POLL_INTERVAL_SECONDS)

        # Clean shutdown on stop()
        if segment_id is not None:
            end_segment(conn, segment_id)
        if session_id is not None:
            end_session(conn, session_id)
        conn.close()