"""
Notification Banners - Premium UI Components
Encapsulates notification display logic and animations.
"""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer, QSize
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
    Green Gradient Banner for Bank Notifications
    Replaces 'notif_box' in MainWindow
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        
        # Style
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                border-radius: 21px;
                padding: 0 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 8, 0)
        layout.setSpacing(10)
        
        # Label
        self.label = QLabel("Đang chờ giao dịch...")
        self.label.setStyleSheet(
            "color: white; font-weight: 700; font-size: 13px; background: transparent; letter-spacing: 0.3px;"
        )
        layout.addWidget(self.label)
        
        # Close Button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.25);
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.close_btn.clicked.connect(self.hide_banner)
        self.close_btn.clicked.connect(self.closed)
        layout.addWidget(self.close_btn)
        
        self.hide()


class SystemNotificationBanner(BaseBanner):
    """
    Indigo Pill Banner for System/Task Notifications
    Replaces 'task_notif_box' in MainWindow
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        
        # Style
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                border-radius: 24px;
                padding: 0 5px;
                margin: 0 0 16px 0;
                border: 1px solid rgba(255, 255, 255, 0.25);
            }
            QFrame:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4F46E5, stop:1 #4338CA);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }
        """)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 8, 0)
        layout.setSpacing(12)
        
        # Icon (Optional, text based for now)
        # icon = QLabel("✨")
        # layout.addWidget(icon)
        
        # Label
        self.label = QLabel("Chưa có việc")
        self.label.setStyleSheet(
            "color: white; font-weight: 800; font-size: 13px; background: transparent; border: none;"
        )
        layout.addWidget(self.label)
        
        # Close Button
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.35);
            }
        """)
        self.close_btn.clicked.connect(self.hide_banner)
        self.close_btn.clicked.connect(self.closed)
        layout.addWidget(self.close_btn)
        
        self.hide()
