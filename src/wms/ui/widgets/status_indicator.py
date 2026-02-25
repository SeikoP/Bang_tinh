"""
Status Indicator Widget - Shows server connection state in sidebar
Provides visual feedback: 🟢 Running / 🔴 Stopped / 🟡 Starting
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QPainter, QColor, QBrush


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
    STATE_NO_NETWORK = "no_network"
    STATE_RECONNECTING = "reconnecting"
    
    _COLORS = {
        STATE_RUNNING: "#22c55e",       # Green
        STATE_STOPPED: "#ef4444",       # Red
        STATE_STARTING: "#f59e0b",      # Yellow  
        STATE_NO_DATA: "#f97316",       # Amber/Orange
        STATE_NO_NETWORK: "#dc2626",    # Dark Red
        STATE_RECONNECTING: "#a855f7",  # Purple
    }
    
    _LABELS = {
        STATE_RUNNING: "Server: ON",
        STATE_STOPPED: "Server: OFF",
        STATE_STARTING: "Starting...",
        STATE_NO_DATA: "No data",
        STATE_NO_NETWORK: "No network",
        STATE_RECONNECTING: "Reconnecting...",
    }

    # Interface type display names
    _INTERFACE_LABELS = {
        "wifi": "WiFi",
        "ethernet": "LAN",
        "loopback": "Local",
        "other": "Network",
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = self.STATE_STARTING
        self._last_notification_time = None
        self._no_data_threshold_ms = 600_000  # 10 minutes
        self._connection_type = ""
        self._device_count = 0
        
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

        # Extra info label (connection type / device count)
        self._info_label = QLabel("")
        self._info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.45);
                font-size: 9px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self._info_label)
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
        self._update_info()

    def set_connection_type(self, conn_type: str):
        """Update the displayed connection type (wifi, ethernet, usb_tether, etc.)."""
        self._connection_type = conn_type
        self._update_info()

    def set_device_count(self, count: int):
        """Update the number of connected Android devices."""
        self._device_count = count
        self._update_info()

    def _update_info(self):
        """Refresh the info label with connection type + device count."""
        parts = []
        if self._connection_type:
            display = self._INTERFACE_LABELS.get(
                self._connection_type, self._connection_type
            )
            parts.append(display)
        if self._device_count > 0:
            parts.append(f"{self._device_count} device{'s' if self._device_count > 1 else ''}")
        self._info_label.setText(" · ".join(parts))
    
    def record_notification(self):
        """Record that a notification was received (for no-data detection)"""
        import time
        self._last_notification_time = int(time.time() * 1000)
    
    def check_no_data(self):
        """Check if we haven't received data in a while"""
        if self._state != self.STATE_RUNNING:
            return
        if self._last_notification_time is None:
            return  # No notifications yet, don't warn
        
        import time
        now = int(time.time() * 1000)
        elapsed = now - self._last_notification_time
        
        if elapsed > self._no_data_threshold_ms:
            self.set_state(self.STATE_NO_DATA)
        elif self._state == self.STATE_NO_DATA:
            self.set_state(self.STATE_RUNNING)
