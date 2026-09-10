"""
Query functions for reading tracked data.
Keeps SQL out of the UI layer.
"""

import sqlite3
from datetime import datetime, timezone


def get_active_seconds_today(conn: sqlite3.Connection) -> float:
    """Sum active-state segment durations that started today (UTC)."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()

    rows = conn.execute(
        """
        SELECT started_at, ended_at
        FROM session_segments
        WHERE state = 'active' AND started_at >= ?
        """,
        (today_start,),
    ).fetchall()

    total_seconds = 0.0
    for started_at, ended_at in rows:
        start = datetime.fromisoformat(started_at)
        # Open segments (no ended_at yet) count up to now.
        end = datetime.fromisoformat(ended_at) if ended_at else datetime.now(timezone.utc)
        total_seconds += (end - start).total_seconds()

    return total_seconds