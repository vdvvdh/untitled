"""
Runs the tracking loop on a background thread, watching every
non-excluded game in the registry (not just one hard-coded target).
"""

import time

from PySide6.QtCore import QThread

from app.database.connection import get_connection
from app.database.migrations import run_migrations
from app.games.registry import get_trackable_games
from app.tracking.focus_detector import get_foreground_process_name
from app.tracking.idle_detector import get_idle_seconds
from app.tracking.state_engine import Observation, classify
from app.tracking.session_manager import (
    is_target_running,
    start_session,
    end_session,
    start_segment,
    end_segment,
)

POLL_INTERVAL_SECONDS = 3


class TrackerThread(QThread):
    def __init__(self):
        super().__init__()
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        conn = get_connection()
        run_migrations(conn)

        # Per-game tracking state: game_id -> {session_id, segment_id, current_state}
        game_state: dict[int, dict] = {}

        while self._running:
            focused = get_foreground_process_name()
            idle_seconds = get_idle_seconds()
            games = get_trackable_games(conn)

            for game_id, name, executable_name in games:
                state = game_state.setdefault(
                    game_id, {"session_id": None, "segment_id": None, "current_state": None}
                )

                running = is_target_running(executable_name)
                focused_match = bool(focused and focused.lower() == executable_name.lower())

                observation = Observation(
                    target_process_running=running,
                    target_process_focused=focused_match,
                    idle_seconds=idle_seconds,
                )
                new_state = classify(observation)

                if running and state["session_id"] is None:
                    state["session_id"] = start_session(conn, game_id)

                if not running and state["session_id"] is not None:
                    if state["segment_id"] is not None:
                        end_segment(conn, state["segment_id"])
                        state["segment_id"] = None
                    end_session(conn, state["session_id"])
                    state["session_id"] = None
                    state["current_state"] = None

                if state["session_id"] is not None and new_state != state["current_state"]:
                    if state["segment_id"] is not None:
                        end_segment(conn, state["segment_id"])
                    state["segment_id"] = start_segment(conn, state["session_id"], new_state)
                    state["current_state"] = new_state

            time.sleep(POLL_INTERVAL_SECONDS)

        # Clean shutdown: close any still-open sessions
        for game_id, state in game_state.items():
            if state["segment_id"] is not None:
                end_segment(conn, state["segment_id"])
            if state["session_id"] is not None:
                end_session(conn, state["session_id"])

        conn.close()