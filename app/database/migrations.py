"""
Numbered SQLite migrations.
Each migration is a plain SQL script applied in order, tracked in
schema_migrations so we never apply the same one twice.
"""

import sqlite3

MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            executable_name TEXT NOT NULL UNIQUE,
            excluded INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """,
    ),
    (
        2,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            is_open INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (game_id) REFERENCES games (id)
        );
        """,
    ),
    (
        3,
        """
        CREATE TABLE IF NOT EXISTS session_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            state TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );
        """,
    ),
]


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply any migrations that haven't been applied yet, in order."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.commit()

    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}

    for version, sql in MIGRATIONS:
        if version in applied:
            continue
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
        conn.commit()
        print(f"Applied migration {version}")


if __name__ == "__main__":
    from app.database.connection import get_connection

    connection = get_connection()
    run_migrations(connection)
    connection.close()
    print("Migrations complete.")