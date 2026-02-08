"""
Alert Panel Widget - Hiển thị cảnh báo tồn kho
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget
)

from ui.qt_theme import AppColors


class AlertPanel(QFrame):
    """Panel hiển thị alerts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedWidth(320)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("⚠️ Cảnh báo")
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {AppColors.TEXT};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #cbd5e1;
                border-radius: 16px;
                background: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #f1f5f9;
            }
        """)
        refresh_btn.clicked.connect(self.refresh_alerts)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Scroll area for alerts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.alerts_container = QWidget()
        self.alerts_layout = QVBoxLayout(self.alerts_container)
        self.alerts_layout.setContentsMargins(0, 0, 0, 0)
        self.alerts_layout.setSpacing(8)
        self.alerts_layout.addStretch()
        
        scroll.setWidget(self.alerts_container)
        layout.addWidget(scroll, 1)
        
        # Empty state
        self.empty_label = QLabel("✅ Không có cảnh báo")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY};
            font-size: 13px;
            padding: 20px;
        """)
        self.alerts_layout.insertWidget(0, self.empty_label)
    
    def update_alerts(self, alerts):
        """Update alerts display"""
        # Clear existing alerts (except empty label)
        while self.alerts_layout.count() > 1:
            item = self.alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not alerts:
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        
        # Add alert widgets
        for alert in alerts:
            alert_widget = self._create_alert_widget(alert)
            self.alerts_layout.insertWidget(self.alerts_layout.count() - 1, alert_widget)
    
    def _create_alert_widget(self, alert):
        """Create widget for single alert"""
        from services.alert_service import AlertLevel
        
        widget = QFrame()
        widget.setObjectName("alert_item")
        
        # Color based on level
        if alert.level == AlertLevel.CRITICAL:
            bg_color = "#FEE2E2"
            border_color = "#DC2626"
            text_color = "#991B1B"
        elif alert.level == AlertLevel.WARNING:
            bg_color = "#FEF3C7"
            border_color = "#F59E0B"
            text_color = "#92400E"
        else:
            bg_color = "#DBEAFE"
            border_color = "#3B82F6"
            text_color = "#1E40AF"
        
        widget.setStyleSheet(f"""
            QFrame#alert_item {{
                background: {bg_color};
                border-left: 4px solid {border_color};
                border-radius: 6px;
                padding: 8px 12px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        # Title
        title = QLabel(alert.title)
        title.setStyleSheet(f"""
            color: {text_color};
            font-weight: 700;
            font-size: 13px;
        """)
        layout.addWidget(title)
        
        # Message
        message = QLabel(alert.message)
        message.setStyleSheet(f"""
            color: {text_color};
            font-size: 12px;
        """)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Timestamp
        time_label = QLabel(alert.timestamp.strftime("%H:%M:%S"))
        time_label.setStyleSheet(f"""
            color: {text_color};
            font-size: 10px;
            font-style: italic;
        """)
        layout.addWidget(time_label)
        
        return widget
    
    def refresh_alerts(self):
        """Refresh alerts from service"""
        # This will be connected to parent's refresh method
        pass
