"""
SQLite connection management.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "tracker.db"


def get_connection() -> sqlite3.Connection:
    """Open a connection to the local SQLite database, creating the folder if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn