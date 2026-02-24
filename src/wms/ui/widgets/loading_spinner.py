"""
Loading Spinner Widget
"""

from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LoadingSpinner(QWidget):
    """
    Animated loading spinner

    Usage:
        spinner = LoadingSpinner()
        spinner.start()
        # ... do work ...
        spinner.stop()
    """

    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)

        self.size = size
        self.angle = 0
        self.is_spinning = False

        self.setFixedSize(size, size)

        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)

    def start(self):
        """Start spinning"""
        self.is_spinning = True
        self.timer.start(50)  # Update every 50ms
        self.show()

    def stop(self):
        """Stop spinning"""
        self.is_spinning = False
        self.timer.stop()
        self.hide()

    def _rotate(self):
        """Rotate spinner"""
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        """Paint spinner"""
        if not self.is_spinning:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 2 - 5

        # Draw arcs
        pen = QPen(QColor("#334e88"))
        pen.setWidth(4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        # Rotate
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)
        painter.translate(-center_x, -center_y)

        # Draw arc
        rect = QRect(center_x - radius, center_y - radius, radius * 2, radius * 2)
        painter.drawArc(rect, 0, 270 * 16)  # 270 degrees


class LoadingOverlay(QWidget):
    """
    Full-screen loading overlay

    Usage:
        overlay = LoadingOverlay(parent_widget)
        overlay.show_loading("Loading...")
        # ... do work ...
        overlay.hide_loading()
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Semi-transparent background
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.5);")

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Spinner
        self.spinner = LoadingSpinner(size=64)
        layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        # Message
        self.message_label = QLabel()
        self.message_label.setStyleSheet("""
            color: white;
            font-size: 16px;
            font-weight: 600;
            padding: 16px;
        """)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        # Initially hidden
        self.hide()

    def show_loading(self, message: str = "Loading..."):
        """Show loading overlay"""
        self.message_label.setText(message)
        self.spinner.start()
        self.show()
        self.raise_()  # Bring to front

        # Resize to parent
        if self.parent():
            self.resize(self.parent().size())

    def hide_loading(self):
        """Hide loading overlay"""
        self.spinner.stop()
        self.hide()

    def resizeEvent(self, event):
        """Handle resize"""
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)
