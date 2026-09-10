"""
Dashboard: total active playtime with range filters, playtime by game,
most recently played, and recent session history.
"""

import sys
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QListWidget,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import get_connection
from app.database.migrations import run_migrations
from app.database.repositories import (
    get_active_seconds_for_range,
    get_playtime_by_game,
    get_most_recently_played,
    get_recent_sessions,
)
from app.tracking.tracker_thread import TrackerThread

REFRESH_INTERVAL_MS = 5000

RANGE_OPTIONS = [
    ("Today", "today"),
    ("Last 7 days", "7days"),
    ("Last 30 days", "30days"),
    ("This month", "month"),
    ("This year", "year"),
    ("All time", "all"),
]


def format_duration(total_seconds: float) -> str:
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def format_timestamp(iso_string: str) -> str:
    dt = datetime.fromisoformat(iso_string)
    return dt.strftime("%Y-%m-%d %H:%M")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gaming Activity Tracker")
        self.resize(420, 500)

        self.range_selector = QComboBox()
        for label, key in RANGE_OPTIONS:
            self.range_selector.addItem(label, key)
        self.range_selector.currentIndexChanged.connect(self.refresh)

        self.total_label = QLabel("Loading...")
        self.total_label.setStyleSheet("font-size: 28px; padding: 10px;")

        self.recent_label = QLabel("Most recently played: —")

        self.by_game_list = QListWidget()
        self.sessions_list = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Time range:"))
        layout.addWidget(self.range_selector)
        layout.addWidget(QLabel("Total active playtime:"))
        layout.addWidget(self.total_label)
        layout.addWidget(self.recent_label)
        layout.addWidget(QLabel("Playtime by game:"))
        layout.addWidget(self.by_game_list)
        layout.addWidget(QLabel("Recent sessions:"))
        layout.addWidget(self.sessions_list)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Ensure the database and tables exist before anything queries them.
        setup_conn = get_connection()
        run_migrations(setup_conn)
        setup_conn.close()

        self.tracker_thread = TrackerThread()
        self.tracker_thread.start()

        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(REFRESH_INTERVAL_MS)

    def refresh(self):
        range_key = self.range_selector.currentData()
        conn = get_connection()

        total_seconds = get_active_seconds_for_range(conn, range_key)
        self.total_label.setText(format_duration(total_seconds))

        recent = get_most_recently_played(conn)
        if recent:
            name, started_at = recent
            self.recent_label.setText(f"Most recently played: {name} ({format_timestamp(started_at)})")
        else:
            self.recent_label.setText("Most recently played: —")

        self.by_game_list.clear()
        for name, seconds in get_playtime_by_game(conn, range_key):
            self.by_game_list.addItem(f"{name}: {format_duration(seconds)}")

        self.sessions_list.clear()
        for name, started_at, ended_at in get_recent_sessions(conn):
            end_str = format_timestamp(ended_at) if ended_at else "in progress"
            self.sessions_list.addItem(f"{name} — {format_timestamp(started_at)} → {end_str}")

        conn.close()

    def closeEvent(self, event):
        self.tracker_thread.stop()
        self.tracker_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()