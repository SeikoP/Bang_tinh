"""
Status Indicator Widget - Shows server connection state in sidebar
Provides visual feedback: 🟢 Running / 🔴 Stopped / 🟡 Starting
"""

import time

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QPainter
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class StatusDot(QWidget):
    """Animated colored circle for status indication"""

    def __init__(self, size=8, parent=None):
        super().__init__(parent)
        self._color = QColor("#22c55e")  # Green by default
        self._size = size
        self.setFixedSize(size + 4, size + 4)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Draw glow effect
        glow = QColor(self._color)
        glow.setAlpha(60)
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(0, 0, self._size + 4, self._size + 4)

        # Draw main dot
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(2, 2, self._size, self._size)
        painter.end()


class StatusIndicator(QFrame):
    """
    Server status indicator widget for sidebar.

    States:
        - RUNNING (green): Server is accepting connections
        - STOPPED (red): Server is not running
        - STARTING (yellow): Server is initializing
        - NO_DATA (amber): Running but no recent notifications
    """

    STATE_RUNNING = "running"
    STATE_STOPPED = "stopped"
    STATE_STARTING = "starting"
    STATE_NO_DATA = "no_data"

    _COLORS = {
        STATE_RUNNING: "#22c55e",  # Green
        STATE_STOPPED: "#ef4444",  # Red
        STATE_STARTING: "#f59e0b",  # Yellow
        STATE_NO_DATA: "#f97316",  # Amber/Orange
    }

    _LABELS = {
        STATE_RUNNING: "Server: ON",
        STATE_STOPPED: "Server: OFF",
        STATE_STARTING: "Starting...",
        STATE_NO_DATA: "No data",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = self.STATE_STARTING
        self._last_notification_time = None
        self._no_data_threshold_ms = 600_000  # 10 minutes

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self._dot = StatusDot(size=8)
        layout.addWidget(self._dot)

        self._label = QLabel(self._LABELS[self._state])
        self._label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 10px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self._label)
        layout.addStretch()

        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                border: none;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to go to Settings")

    def set_state(self, state: str):
        """Update the indicator state"""
        if state == self._state:
            return
        self._state = state
        color = self._COLORS.get(state, self._COLORS[self.STATE_STOPPED])
        label = self._LABELS.get(state, "Unknown")
        self._dot.set_color(color)
        self._label.setText(label)

    def record_notification(self):
        """Record that a notification was received (for no-data detection)"""
        self._last_notification_time = int(time.time() * 1000)

    def check_no_data(self):
        """Check if we haven't received data in a while"""
        if self._state != self.STATE_RUNNING:
            return
        if self._last_notification_time is None:
            return  # No notifications yet, don't warn

        now = int(time.time() * 1000)
        elapsed = now - self._last_notification_time

        if elapsed > self._no_data_threshold_ms:
            self.set_state(self.STATE_NO_DATA)
        elif self._state == self.STATE_NO_DATA:
            self.set_state(self.STATE_RUNNING)
