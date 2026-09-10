"""
Query functions for reading tracked data.
Keeps SQL out of the UI layer.
"""

import sqlite3
from datetime import datetime, timedelta, timezone


def _range_start(range_key: str) -> str | None:
    """Return an ISO timestamp marking the start of the given range, or None for all-time."""
    now = datetime.now(timezone.utc)

    if range_key == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_key == "7days":
        start = now - timedelta(days=7)
    elif range_key == "30days":
        start = now - timedelta(days=30)
    elif range_key == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_key == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_key == "all":
        return None
    else:
        raise ValueError(f"Unknown range: {range_key}")

    return start.isoformat()


def _sum_active_seconds(rows) -> float:
    total = 0.0
    for started_at, ended_at in rows:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at) if ended_at else datetime.now(timezone.utc)
        total += (end - start).total_seconds()
    return total


def get_active_seconds_for_range(conn: sqlite3.Connection, range_key: str) -> float:
    """Total active-state seconds across all games within the given range."""
    range_start = _range_start(range_key)

    if range_start:
        rows = conn.execute(
            "SELECT started_at, ended_at FROM session_segments WHERE state = 'active' AND started_at >= ?",
            (range_start,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT started_at, ended_at FROM session_segments WHERE state = 'active'"
        ).fetchall()

    return _sum_active_seconds(rows)


def get_playtime_by_game(conn: sqlite3.Connection, range_key: str) -> list[tuple[str, float]]:
    """List of (game_name, active_seconds) within the given range, sorted descending."""
    range_start = _range_start(range_key)

    query = """
        SELECT g.name, seg.started_at, seg.ended_at
        FROM session_segments seg
        JOIN sessions s ON seg.session_id = s.id
        JOIN games g ON s.game_id = g.id
        WHERE seg.state = 'active'
    """
    params: tuple = ()
    if range_start:
        query += " AND seg.started_at >= ?"
        params = (range_start,)

    rows = conn.execute(query, params).fetchall()

    totals: dict[str, float] = {}
    for name, started_at, ended_at in rows:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at) if ended_at else datetime.now(timezone.utc)
        totals[name] = totals.get(name, 0.0) + (end - start).total_seconds()

    return sorted(totals.items(), key=lambda item: item[1], reverse=True)


def get_most_recently_played(conn: sqlite3.Connection) -> tuple[str, str] | None:
    """Return (game_name, started_at) of the most recent session, or None."""
    row = conn.execute(
        """
        SELECT g.name, s.started_at
        FROM sessions s
        JOIN games g ON s.game_id = g.id
        ORDER BY s.started_at DESC
        LIMIT 1
        """
    ).fetchone()
    return tuple(row) if row else None


def get_recent_sessions(conn: sqlite3.Connection, limit: int = 10) -> list[tuple]:
    """Return recent sessions as (game_name, started_at, ended_at)."""
    return conn.execute(
        """
        SELECT g.name, s.started_at, s.ended_at
        FROM sessions s
        JOIN games g ON s.game_id = g.id
        ORDER BY s.started_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()