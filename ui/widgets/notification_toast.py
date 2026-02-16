"""
Toast Notification Widget
"""

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtWidgets import (QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                             QPushButton, QWidget)


class NotificationToast(QWidget):
    """
    Toast notification widget

    Usage:
        toast = NotificationToast(parent_widget)
        toast.show_message("Success!", type="success")
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        layout.addWidget(self.icon_label)

        # Message
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label, stretch=1)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)
        close_btn.clicked.connect(self.hide_toast)
        layout.addWidget(close_btn)

        # Opacity effect for fade animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        # Auto-hide timer
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_toast)

        # Initially hidden
        self.hide()

    def show_message(
        self,
        message: str,
        type: str = "info",
        duration: int = 3000,
        position: str = "top-right",
    ):
        """
        Show toast message

        Args:
            message: Message text
            type: Message type (success, error, warning, info)
            duration: Duration in milliseconds (0 = no auto-hide)
            position: Position (top-right, top-left, bottom-right, bottom-left, center)
        """
        # Set message
        self.message_label.setText(message)

        # Set style based on type
        styles = {
            "success": {"bg": "#4caf50", "icon": "✓"},
            "error": {"bg": "#f44336", "icon": "✗"},
            "warning": {"bg": "#ff9800", "icon": "⚠"},
            "info": {"bg": "#2196f3", "icon": "ℹ"},
        }

        style = styles.get(type, styles["info"])

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {style['bg']};
                border-radius: 8px;
                color: white;
            }}
            QLabel {{
                color: white;
                font-size: 14px;
                font-weight: 500;
            }}
        """)

        self.icon_label.setText(style["icon"])
        self.icon_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
        """)

        # Adjust size
        self.adjustSize()
        self.setFixedWidth(min(400, self.width()))

        # Position
        self._position_toast(position)

        # Show with fade-in animation
        self.show()
        self._fade_in()

        # Auto-hide
        if duration > 0:
            self.hide_timer.start(duration)

    def _position_toast(self, position: str):
        """Position toast on screen"""
        if not self.parent():
            return

        parent_rect = self.parent().rect()
        toast_width = self.width()
        toast_height = self.height()
        margin = 20

        positions = {
            "top-right": QPoint(parent_rect.width() - toast_width - margin, margin),
            "top-left": QPoint(margin, margin),
            "bottom-right": QPoint(
                parent_rect.width() - toast_width - margin,
                parent_rect.height() - toast_height - margin,
            ),
            "bottom-left": QPoint(margin, parent_rect.height() - toast_height - margin),
            "center": QPoint(
                (parent_rect.width() - toast_width) // 2,
                (parent_rect.height() - toast_height) // 2,
            ),
        }

        pos = positions.get(position, positions["top-right"])
        self.move(pos)

    def _fade_in(self):
        """Fade in animation"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

    def _fade_out(self):
        """Fade out animation"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.animation.finished.connect(self.hide)
        self.animation.start()

    def hide_toast(self):
        """Hide toast with fade-out"""
        self.hide_timer.stop()
        self._fade_out()
