"""
Notification Banners - Premium UI Components
Encapsulates notification display logic and animations.
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer, QSize, QRect
from PyQt6.QtGui import QPainter, QLinearGradient, QColor, QFont
from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QGraphicsOpacityEffect, QWidget


class BaseBanner(QFrame):
    """Base class for notification banners with animations"""
    
    clicked = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Setup Opacity Effect for Fade Animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)
        
        # Slide animation (width)
        self.slide_anim = QPropertyAnimation(self, b"maximumWidth")
        self.slide_anim.setDuration(400)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutBack)
        
        # Auto-hide timer
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_banner)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def show_message(self, message: str, duration: int = 0):
        """Show message with animation"""
        self.label.setText(message)
        self.show()
        
        # Reset values
        self.opacity_effect.setOpacity(0)
        self.setMaximumWidth(0)
        
        # Animations
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
        self.slide_anim.setStartValue(0)
        self.slide_anim.setEndValue(500) # Max width
        self.slide_anim.start()
        
        if duration > 0:
            self.timer.start(duration)
        else:
            self.timer.stop()

    def hide_banner(self):
        """Hide with animation"""
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self.hide)
        self.fade_anim.start()


class BankNotificationBanner(BaseBanner):
    """
    Compact Pill Banner for Bank Notifications
    Designed to be slim and tidy on the topbar.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)  # Compact height
        self.setMaximumWidth(320)  # Limit width to stay compact
        
        # Style: Modern Glassmorphism/Solid blend
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #10b981);
                border-radius: 15px;
                padding: 0px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 3, 0)
        layout.setSpacing(6)
        
        # Icon/Indicator
        self.dot = QFrame()
        self.dot.setFixedSize(7, 7)
        self.dot.setStyleSheet("background: #fdf2f2; border-radius: 3px;")
        layout.addWidget(self.dot)
        
        # Label
        self.label = QLabel("Đang chờ...")
        self.label.setStyleSheet(
            "color: white; font-weight: 700; font-size: 12px; background: transparent;"
        )
        layout.addWidget(self.label)
        
        layout.addStretch()
        
        # Close Button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: none;
                border-radius: 11px;
                font-weight: bold;
                font-size: 9px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        self.close_btn.clicked.connect(self.hide_banner)
        self.close_btn.clicked.connect(self.closed)
        layout.addWidget(self.close_btn)
        
        self.hide()
    
    def show_message(self, message: str, duration: int = 0):
        """Show message with animation (override to set proper max width)"""
        self.label.setText(message)
        self.show()
        
        # Reset values
        self.opacity_effect.setOpacity(0)
        self.setMaximumWidth(0)
        
        # Animations
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        
        self.slide_anim.setStartValue(0)
        self.slide_anim.setEndValue(320)  # Match compact max width
        self.slide_anim.start()
        
        if duration > 0:
            self.timer.start(duration)
        else:
            self.timer.stop()


class SystemNotificationBanner(QFrame):
    """
    Bottom Ticker Bar for System/Task/Android Test Notifications.
    Shows as a slim line at the bottom of the app with scrolling text.
    """

    clicked = pyqtSignal()
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(28)

        # Messages queue (most-recent first)
        self._messages: list[str] = []
        self._scroll_offset = 0.0

        # Style – indigo gradient bar
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5, stop:0.5 #6366F1, stop:1 #4F46E5);
                border: none;
                border-top: 1px solid rgba(255, 255, 255, 0.15);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(6)

        # Prefix icon
        icon_lbl = QLabel("ℹ")
        icon_lbl.setStyleSheet(
            "color: rgba(255,255,255,0.7); font-size: 12px; background: transparent; border: none;"
        )
        icon_lbl.setFixedWidth(16)
        layout.addWidget(icon_lbl)

        # Scrolling label
        self.label = QLabel("")
        self.label.setStyleSheet(
            "color: white; font-weight: 600; font-size: 11px; background: transparent; border: none;"
        )
        layout.addWidget(self.label, 1)

        # Close button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: white; border: none; border-radius: 10px;
                font-size: 9px; font-weight: bold;
            }
            QPushButton:hover { background: rgba(255,255,255,0.3); }
        """)
        self.close_btn.clicked.connect(self.hide_banner)
        self.close_btn.clicked.connect(self.closed)
        layout.addWidget(self.close_btn)

        # Auto-hide timer
        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self.hide_banner)

        # Fade effect
        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._fade = QPropertyAnimation(self._opacity, b"opacity")
        self._fade.setDuration(250)

        self.hide()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def show_message(self, message: str, duration: int = 0):
        """Show a message in the ticker bar."""
        # Prepend timestamp for multi-message awareness
        self._messages.insert(0, message)
        if len(self._messages) > 20:
            self._messages = self._messages[:20]

        self.label.setText(message)
        self.show()

        # Fade-in
        self._opacity.setOpacity(0)
        self._fade.stop()
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.start()

        if duration > 0:
            self._auto_timer.start(duration)
        else:
            self._auto_timer.stop()

    def hide_banner(self):
        """Fade out then hide."""
        self._fade.stop()
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self._on_fade_out_done)
        self._fade.start()

    def _on_fade_out_done(self):
        self.hide()
        try:
            self._fade.finished.disconnect(self._on_fade_out_done)
        except TypeError:
            pass
