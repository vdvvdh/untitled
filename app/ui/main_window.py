"""
Minimal dashboard: shows total active playtime today.
Reads from the database on a timer — does not touch processes,
windows, or SQL directly (that's the tracking and repository layers).
"""

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from app.database.connection import get_connection
from app.database.repositories import get_active_seconds_today

REFRESH_INTERVAL_MS = 5000


def format_duration(total_seconds: float) -> str:
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gaming Activity Tracker")
        self.resize(300, 150)

        self.label = QLabel("Loading...")
        self.label.setStyleSheet("font-size: 28px; padding: 20px;")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Active playtime today:"))
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(REFRESH_INTERVAL_MS)

    def refresh(self):
        conn = get_connection()
        seconds = get_active_seconds_today(conn)
        conn.close()
        self.label.setText(format_duration(seconds))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()