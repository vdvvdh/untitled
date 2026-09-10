"""
Game registry: lets the tracker watch multiple executables instead
of one hard-coded target. Games are stored in the database, so adding
a new one doesn't require touching source code.
"""

import sqlite3


def add_game(conn: sqlite3.Connection, name: str, executable_name: str) -> int:
    """Add a new trackable game, or return the existing id if it's already registered."""
    existing = conn.execute(
        "SELECT id FROM games WHERE executable_name = ?", (executable_name,)
    ).fetchone()
    if existing:
        return existing[0]

    cursor = conn.execute(
        "INSERT INTO games (name, executable_name) VALUES (?, ?)",
        (name, executable_name),
    )
    conn.commit()
    return cursor.lastrowid


def exclude_game(conn: sqlite3.Connection, executable_name: str) -> None:
    """Mark a registered game as excluded, so it's tracked in the DB but ignored."""
    conn.execute(
        "UPDATE games SET excluded = 1 WHERE executable_name = ?", (executable_name,)
    )
    conn.commit()


def include_game(conn: sqlite3.Connection, executable_name: str) -> None:
    """Reverse an exclusion."""
    conn.execute(
        "UPDATE games SET excluded = 0 WHERE executable_name = ?", (executable_name,)
    )
    conn.commit()


def get_trackable_games(conn: sqlite3.Connection) -> list[tuple[int, str, str]]:
    """Return (id, name, executable_name) for every non-excluded registered game."""
    return conn.execute(
        "SELECT id, name, executable_name FROM games WHERE excluded = 0"
    ).fetchall()