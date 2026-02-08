"""
Main Application - Phần mềm Quản lý Xuất kho & Dịch vụ
PyQt6 Version - Modern Premium Design - Refactored
"""

import html
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QEvent, Qt, QThread, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup, QSequentialAnimationGroup
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QStackedWidget, QTabWidget, QVBoxLayout, QWidget, QGraphicsOpacityEffect
)

from database.connection import init_db
from config import (
    APP_NAME, APP_VERSION, WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_WIDTH
)
from ui.qt_theme import AppColors, AppTheme

# Import centralized paths
try:
    from app.core.paths import ASSETS
except ImportError:
    if getattr(sys, "frozen", False):
        ASSETS = Path(sys._MEIPASS) / "assets"
    else:
        ASSETS = Path(__file__).parent / "assets"

# Import views
from ui.qt_views.calculation_view import CalculationView
from ui.qt_views.history_view import HistoryView
from ui.qt_views.product_view import ProductView
from ui.qt_views.settings_view import SettingsView
from ui.qt_views.stock_view import StockView
from ui.qt_views.task_view import TaskView
from ui.qt_views.calculator_tool_view import CalculatorToolView
from ui.views.bank_view import BankView
from ui.widgets.quick_bank_peek import QuickBankPeek

# Import network components
from network.notification_server import NotificationServer
from workers.notification_processor import NotificationProcessor

# Initialize database
init_db()


# BankView, NotificationHandler, NotificationServer, QuickBankPeek
# have been moved to separate files for better organization


class MainWindow(QMainWindow):
    """Main window - modern premium design"""

    # Signal for cross-thread notification
    notification_received = pyqtSignal(str)

    def __init__(self, container=None):
        super().__init__()
        # Inject dependency container
        from core.config import Config
        from core.container import Container

        if container is None:
            # Fallback: create default container if not provided
            config = Config.from_env()
            container = Container(config)

        self.container = container
        self.logger = container.get("logger")
        self.config = container.get("config")
        self.error_handler = None  # Will be initialized in _setup_ui

        # Production mode checks
        if self.config and self.config.environment == "production":
            self.logger.info("Running in PRODUCTION mode")
            self._production_mode = True
        else:
            self._production_mode = False
            if self.config:
                self.logger.info(f"Running in {self.config.environment.upper()} mode")

        # Initialize notification processor worker
        self._notification_processor = NotificationProcessor(logger=self.logger)
        self._notification_processor.notification_processed.connect(self._handle_processed_notification)
        self._notification_processor.error_occurred.connect(self._handle_notification_error)
        
        # Initialize TTS service
        from services.tts_service import TTSService
        self._tts_service = TTSService(logger=self.logger)
        self._tts_service.set_enabled(True)  # Enable by default
        self._tts_service.set_voice("edge_female")  # Use Premium Edge TTS (Hoai My)
        self._tts_service.error_occurred.connect(self._on_tts_error)
        
        # Register TTS service in container for settings access
        self.container.register_singleton("tts_service", self._tts_service)
        
        # Get services from container
        self.command_history = self.container.get("command_history")
        self.backup_service = self.container.get("backup_service")
        self.alert_service = self.container.get("alert_service")
        
        # Register alert handler
        if self.alert_service:
            self.alert_service.register_handler(self._on_alert_triggered)

        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._setup_animations()  # Moved after _setup_ui
        self._setup_keyboard_shortcuts()

        # Start notification server
        self._start_notification_server()

        # Timer để ẩn Quick Peek có độ trễ nhỏ (tránh flickering)
        self._peek_timer = QTimer()
        self._peek_timer.setSingleShot(True)
        self._peek_timer.timeout.connect(self._hide_peek_safe)
        
        # Timer for alert checking (every 5 minutes)
        self._alert_timer = QTimer()
        self._alert_timer.timeout.connect(self._check_alerts)
        self._alert_timer.start(300000)  # 5 minutes
        
        # Timer for daily backup (check every hour)
        self._backup_timer = QTimer()
        self._backup_timer.timeout.connect(self._check_daily_backup)
        self._backup_timer.start(3600000)  # 1 hour
        
        # Create startup backup
        if self.backup_service:
            try:
                backup_file = self.backup_service.auto_backup_on_startup()
                if backup_file:
                    self.logger.info(f"Startup backup created: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Startup backup failed: {e}")
    
    def _setup_animations(self):
        """Setup animations for UI elements"""
        # Fade animation for content stack
        self.fade_effect = QGraphicsOpacityEffect(self.content_stack)
        self.content_stack.setGraphicsEffect(self.fade_effect)
        
        self.fade_animation = QPropertyAnimation(self.fade_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Notification slide animations
        self.notif_slide_in = QPropertyAnimation(self.notif_box, b"maximumWidth")
        self.notif_slide_in.setDuration(400)
        self.notif_slide_in.setStartValue(0)
        self.notif_slide_in.setEndValue(500)
        self.notif_slide_in.setEasingCurve(QEasingCurve.Type.OutBack)
        
        self.notif_fade = QGraphicsOpacityEffect(self.notif_box)
        self.notif_box.setGraphicsEffect(self.notif_fade)
        self.notif_fade_anim = QPropertyAnimation(self.notif_fade, b"opacity")
        self.notif_fade_anim.setDuration(300)
        self.notif_fade_anim.setStartValue(0.0)
        self.notif_fade_anim.setEndValue(1.0)
        
        # Task notification animations
        self.task_notif_fade = QGraphicsOpacityEffect(self.task_notif_box)
        self.task_notif_box.setGraphicsEffect(self.task_notif_fade)
        self.task_notif_fade_anim = QPropertyAnimation(self.task_notif_fade, b"opacity")
        self.task_notif_fade_anim.setDuration(300)
        self.task_notif_fade_anim.setStartValue(0.0)
        self.task_notif_fade_anim.setEndValue(1.0)

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        icon_path = ASSETS / "icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                self.setWindowIcon(icon)

        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - WINDOW_WIDTH) // 2
        y = (screen.height() - WINDOW_HEIGHT) // 2
        self.move(x, y)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar - Modern gradient design
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(140)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E293B, stop:0.5 #0F172A, stop:1 #020617);
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 16, 10, 16)
        sidebar_layout.setSpacing(6)

        logo = QLabel("📦 BANGLA")
        logo.setStyleSheet("""
            color: white; 
            font-weight: 950; 
            font-size: 17px; 
            padding: 8px 8px 16px 8px;
            letter-spacing: 1px;
            border-radius: 8px;
        """)
        sidebar_layout.addWidget(logo)

        self.nav_btns = []
        self._add_nav_btn(sidebar_layout, "📊 Quản lý", 0)
        self._add_nav_btn(sidebar_layout, "📋 Ghi chú", 1)
        self._add_nav_btn(sidebar_layout, "💰 Bank", 2)
        self._add_nav_btn(sidebar_layout, "📜 Lịch sử", 3)
        self._add_nav_btn(sidebar_layout, "⚙️ Cài đặt", 4)
        self._add_nav_btn(sidebar_layout, "🔢 Máy tính", 5)

        sidebar_layout.addStretch()
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"""
            color: {AppColors.SIDEBAR_TEXT}; 
            font-size: 10px; 
            padding: 12px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)
        sidebar_layout.addWidget(version)

        main_layout.addWidget(self.sidebar)

        # Content
        self.content_stack = QStackedWidget()
        self._create_views()
        
        # Create management view with sub-tabs
        self.management_view = QWidget()
        management_layout = QVBoxLayout(self.management_view)
        management_layout.setContentsMargins(0, 0, 0, 0)
        management_layout.setSpacing(0)
        
        # Sub-tabs for management
        self.management_tabs = QTabWidget()
        self.management_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                padding: 12px 28px;
                font-weight: 600;
                font-size: 13px;
                background: transparent;
                color: {AppColors.TEXT_SECONDARY};
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {AppColors.PRIMARY};
                border-bottom: 2px solid {AppColors.PRIMARY};
                background: rgba(37, 99, 235, 0.05);
            }}
            QTabBar::tab:hover:!selected {{
                color: {AppColors.TEXT};
                background: rgba(15, 23, 42, 0.05);
            }}
        """)
        
        self.management_tabs.addTab(self.calc_view, "🧮 Tính tiền")
        
        # Create product list tab from calc_view's prod_tab
        self.product_list_tab = self.calc_view.prod_tab
        self.management_tabs.addTab(self.product_list_tab, "📦 Danh sách sản phẩm")
        
        self.management_tabs.addTab(self.stock_view, "📊 Kho hàng")
        self.management_tabs.addTab(self.product_view, "📦 Sản phẩm")
        
        management_layout.addWidget(self.management_tabs)
        
        self.content_stack.addWidget(self.management_view)
        self.content_stack.addWidget(self.task_view)
        self.content_stack.addWidget(self.bank_view)
        self.content_stack.addWidget(self.history_view)
        self.content_stack.addWidget(self.settings_view)
        self.content_stack.addWidget(self.calculator_view)

        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Global Header - Modern gradient
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #FFFFFF, stop:1 #F9FAFB);
            border-bottom: 2px solid {AppColors.BORDER};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.breadcrumb = QLabel("🏠 Trang chủ › Bảng tính")
        self.breadcrumb.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY}; 
            font-weight: 600; 
            font-size: 13px;
            letter-spacing: 0.3px;
        """)
        header_layout.addWidget(self.breadcrumb)

        header_layout.addStretch()

        # Bank Notification Widget (Toast-like in header) - Modern gradient design
        self.notif_box = QFrame()
        self.notif_box.setFixedHeight(42)
        self.notif_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_box.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10B981, stop:1 #059669);
                border-radius: 21px;
                padding: 0 6px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
                border: 2px solid rgba(255, 255, 255, 0.5);
            }}
        """)
        self.notif_box.mousePressEvent = lambda e: self._switch_view(2)
        self.notif_box.installEventFilter(self)

        notif_layout = QHBoxLayout(self.notif_box)
        notif_layout.setContentsMargins(16, 0, 8, 0)
        notif_layout.setSpacing(10)

        self.notif_label = QLabel("Đang chờ giao dịch...")
        self.notif_label.setStyleSheet(
            "color: white; font-weight: 700; font-size: 13px; background: transparent; letter-spacing: 0.3px;"
        )
        notif_layout.addWidget(self.notif_label)

        # Nút đóng thông báo (X) - Modern design
        self.notif_close_btn = QPushButton("✕")
        self.notif_close_btn.setFixedSize(30, 30)
        self.notif_close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_close_btn.setStyleSheet("""
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
        self.notif_close_btn.clicked.connect(self.notif_box.hide)
        notif_layout.addWidget(self.notif_close_btn)

        self.notif_box.hide()
        header_layout.addWidget(self.notif_box)

        content_layout.addWidget(header)
        content_layout.addWidget(self.content_stack)
        
        # Task Notification Widget at bottom - Premium Indigo Pill Design
        self.task_notif_box = QFrame()
        self.task_notif_box.setFixedHeight(48)
        self.task_notif_box.setCursor(Qt.CursorShape.PointingHandCursor)
        # Use a pill design that doesn't span the full width
        self.task_notif_box.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #4F46E5);
                border-radius: 24px;
                padding: 0 5px;
                margin: 0 0 16px 0;
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            QFrame:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #4F46E5, stop:1 #4338CA);
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
        """)
        self.task_notif_box.mousePressEvent = lambda e: self._switch_view(1)

        task_notif_layout = QHBoxLayout(self.task_notif_box)
        task_notif_layout.setContentsMargins(20, 0, 8, 0)
        task_notif_layout.setSpacing(12)

        self.task_notif_label = QLabel("Chưa có việc")
        self.task_notif_label.setStyleSheet(
            "color: white; font-weight: 800; font-size: 13px; background: transparent; border: none;"
        )
        task_notif_layout.addWidget(self.task_notif_label)

        # Close button - Modern design
        self.task_notif_close_btn = QPushButton("✕")
        self.task_notif_close_btn.setFixedSize(30, 30)
        self.task_notif_close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.task_notif_close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.35);
            }
        """)
        self.task_notif_close_btn.clicked.connect(self.task_notif_box.hide)
        task_notif_layout.addWidget(self.task_notif_close_btn)

        self.task_notif_box.hide()
        
        # Add to content_layout with alignment
        notif_container = QHBoxLayout()
        notif_container.addStretch()
        notif_container.addWidget(self.task_notif_box)
        notif_container.addStretch()
        content_layout.addLayout(notif_container)
        
        main_layout.addWidget(main_content)

        self._switch_view(0)

    def _add_nav_btn(self, layout, text, index):
        btn = QPushButton(text)
        btn.setObjectName("navItem")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_view(index))

        # Nhấn giữ nút bên trái vẫn dùng hold
        if index == 2:  # Bank view is now at index 2
            self.bank_btn = btn
            btn.pressed.connect(self._start_bank_hold)
            btn.released.connect(self._stop_bank_hold)
            self._hold_timer = QTimer()
            self._hold_timer.setSingleShot(True)
            self._hold_timer.timeout.connect(self._on_bank_hold_success)

        layout.addWidget(btn)
        self.nav_btns.append(btn)

    def eventFilter(self, source, event):
        """Xử lý sự kiện di chuyển chuột (Hover)"""
        if source == self.notif_box:
            if event.type() == QEvent.Type.Enter:
                self._show_peek_under_notif()
            elif event.type() == QEvent.Type.Leave:
                # Đợi một chút rồi mới ẩn để người dùng có thể di chuyển chuột vào bảng
                self._peek_timer.start(200)

        if hasattr(self, "quick_peek") and source == self.quick_peek:
            if event.type() == QEvent.Type.Enter:
                self._peek_timer.stop()  # Hủy lệnh ẩn nếu chuột đi vào bảng
            elif event.type() == QEvent.Type.Leave:
                self._peek_timer.start(200)

        return super().eventFilter(source, event)

    def _show_peek_under_notif(self):
        """Hiện danh sách nhanh dưới thanh thông báo"""
        if not hasattr(self, "quick_peek"):
            self.quick_peek = QuickBankPeek(self)
            self.quick_peek.installEventFilter(self)

        self.quick_peek.update_data(self.bank_view.table)
        pos = self.notif_box.mapToGlobal(self.notif_box.rect().bottomLeft())
        self.quick_peek.move(pos.x(), pos.y() + 5)
        self.quick_peek.show()
        self._peek_timer.stop()

    def _hide_peek_safe(self):
        if hasattr(self, "quick_peek"):
            self.quick_peek.hide()

    def _start_bank_hold(self):
        self._hold_timer.start(500)  # Nhấn giữ 0.5 giây

    def _stop_bank_hold(self):
        self._hold_timer.stop()

    def _on_bank_hold_success(self):
        """Khi nhấn giữ nút Sidebar -> Hiện danh sách nhanh"""
        if not hasattr(self, "quick_peek"):
            self.quick_peek = QuickBankPeek(self)
            self.quick_peek.installEventFilter(self)

        self.quick_peek.update_data(self.bank_view.table)
        btn_pos = self.bank_btn.mapToGlobal(self.bank_btn.rect().topRight())
        self.quick_peek.move(btn_pos.x() + 10, btn_pos.y())
        self.quick_peek.show()
        self._peek_timer.stop()

    def _on_bank_hold_success(self):
        """Khi nhấn giữ đủ lâu, hiện cửa sổ xem nhanh"""
        if not hasattr(self, "quick_peek"):
            self.quick_peek = QuickBankPeek(self)

        self.quick_peek.update_data(self.bank_view.table)

        # Tính toán vị trí hiển thị ngay cạnh sidebar
        btn_pos = self.bank_btn.mapToGlobal(self.bank_btn.rect().topRight())
        self.quick_peek.move(btn_pos.x() + 10, btn_pos.y())
        self.quick_peek.show()

    def _switch_view(self, index):
        """Switch view with fade animation"""
        if self.content_stack.currentIndex() == index:
            return
        
        try:
            # Check if animations are ready
            if not hasattr(self, 'fade_effect') or not hasattr(self, 'fade_animation'):
                # Fallback to direct switch without animation
                self._switch_view_direct(index)
                return
            
            # Fade out current view
            self._fade_out_anim = QPropertyAnimation(self.fade_effect, b"opacity")
            self._fade_out_anim.setDuration(150)
            self._fade_out_anim.setStartValue(1.0)
            self._fade_out_anim.setEndValue(0.0)
            self._fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
            
            def switch_and_fade_in():
                self.content_stack.setCurrentIndex(index)
                icons = ["📊", "📋", "💰", "📜", "⚙️", "🔢"]
                names = ["Quản lý", "Ghi chú", "Bank", "Lịch sử", "Cài đặt", "Máy tính"]
                self.breadcrumb.setText(f"🏠 Trang chủ › {icons[index]} {names[index]}")
                
                # Update nav buttons
                for i, btn in enumerate(self.nav_btns):
                    btn.setProperty("active", i == index)
                    btn.style().unpolish(btn)
                    btn.style().polish(btn)
                
                # Fade in new view
                self.fade_animation.start()
            
            self._fade_out_anim.finished.connect(switch_and_fade_in)
            self._fade_out_anim.start()
        except Exception as e:
            # Fallback to direct switch if animation fails
            self.logger.error(f"Animation error: {e}")
            self._switch_view_direct(index)
    
    def _switch_view_direct(self, index):
        """Switch view directly without animation (fallback)"""
        self.content_stack.setCurrentIndex(index)
        icons = ["📊", "📋", "💰", "📜", "⚙️", "🔢"]
        names = ["Quản lý", "Ghi chú", "Bank", "Lịch sử", "Cài đặt", "Máy tính"]
        self.breadcrumb.setText(f"🏠 Trang chủ › {icons[index]} {names[index]}")
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _create_views(self):
        # Initialize error handler
        from utils.error_handler import ErrorHandler

        self.error_handler = ErrorHandler(self.logger)

        # Pass container to views
        self.calc_view = CalculationView(
            container=self.container, on_refresh_stock=self._refresh_stock
        )
        self.stock_view = StockView(on_refresh_calc=self._refresh_calc)
        self.product_view = ProductView(
            container=self.container, on_refresh_calc=self._refresh_calc
        )
        self.task_view = TaskView(container=self.container)
        self.bank_view = BankView()
        self.history_view = HistoryView()
        self.settings_view = SettingsView(container=self.container)
        self.calculator_view = CalculatorToolView()

        # Connect signals for settings real-time updates
        self.settings_view.row_height_changed.connect(self._on_row_height_changed)
        self.settings_view.widget_height_changed.connect(self._on_widget_height_changed)
    
    def _refresh_stock(self):
        """Refresh stock list in calculation view"""
        if hasattr(self, "calc_view"):
            self.calc_view.refresh_stock_list()

    def _start_notification_server(self):
        """Khởi chạy server ngầm để nhận thông báo"""
        # Get notification service from container
        notification_service = self.container.get("notification")
        if notification_service:
            notification_service.register_handler(self._process_notification)
            notification_service.start_server()
            self.logger.info("Notification server started successfully")
        else:
            # Fallback to direct implementation
            config = self.container.get("config")
            if config:
                self.notif_thread = NotificationServer(
                    host=config.notification_host,
                    port=config.notification_port,
                    logger=self.logger,
                )
            else:
                self.notif_thread = NotificationServer(logger=self.logger)
            self.notif_thread.msg_received.connect(self._process_notification)
            self.notif_thread.start()

    def _process_notification(self, message):
        """Process notification using worker"""
        self._notification_processor.process_notification(message)

    def _handle_processed_notification(self, data: dict):
        """Handle processed notification data from worker"""
        # Handle special commands first (Ping success, Session update etc)
        # to avoid KeyError when accessing fields like amount or has_amount
        if data.get('has_command'):
            timestamp = data.get('timestamp', '')
            cmd = data.get('command')
            
            # Change notif_box color to INFO (Emerald Dark or Blue) for system/command events
            self.notif_label.setText(f"<b>{timestamp}</b> | ✨ {data['content']}")
            self.notif_box.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {AppColors.INFO}, stop:1 {AppColors.PRIMARY});
                    border-radius: 21px;
                    padding: 0 6px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }}
            """)
            self._show_notification_animated()
            
            if cmd == 'REFRESH_SESSION':
                self._refresh_calc()
            
            return

        # Update UI with processed data for normal notifications
        timestamp = data.get('timestamp', '')
        source = data.get('source', '')
        amount = data.get('amount', '')
        sender_name = data.get('sender_name', '')
        content = data.get('content', '')
        has_amount = data.get('has_amount', False)

        if has_amount:
            safe_sender = html.escape(sender_name[:30]) if sender_name else ""
            safe_source = html.escape(source)
            safe_amount = html.escape(amount)

            if safe_sender:
                rich_text = f"<b style='font-size:15px; color:white;'>{timestamp}</b> | <b style='font-size:15px; color:white;'>{safe_amount}</b> | <span style='font-size:12px; color:#e1f5fe;'>{safe_sender}</span>"
            else:
                rich_text = f"<b style='font-size:15px; color:white;'>{timestamp}</b> | <b style='font-size:15px; color:white;'>{safe_amount}</b> | <span style='font-size:11px; color:#e1f5fe;'>{safe_source}</span>"

            self.notif_label.setText(rich_text)
            
            # Reset notification box to Emerald Green (SUCCESS) gradient
            self.notif_box.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #10B981, stop:1 #059669);
                    border-radius: 21px;
                    padding: 0 6px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }}
                QFrame:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #059669, stop:1 #047857);
                    border: 2px solid rgba(255, 255, 255, 0.5);
                }}
            """)
            
            # Animate notification appearance
            self._show_notification_animated()
            
            # Speak notification using TTS
            if self._tts_service and amount:
                self._tts_service.speak_transaction(amount, sender_name)

        if hasattr(self, "bank_view"):
            # Always add to raw logs
            self.bank_view.add_raw_log(timestamp, source, content)

            # Only add to transactions if it has amount
            if has_amount:
                self.bank_view.add_notif(timestamp, source, amount, sender_name, content)
        else:
            if self.logger:
                self.logger.warning("bank_view not initialized yet, notification not saved")
    
    def _show_notification_animated(self):
        """Show notification with slide and fade animation"""
        self.notif_box.setMaximumWidth(0)
        self.notif_box.show()
        
        # Parallel animation: slide + fade
        self.notif_slide_in.start()
        self.notif_fade_anim.start()
        
        # Add bounce effect
        QTimer.singleShot(400, self._bounce_notification)
    
    def _bounce_notification(self):
        """Add subtle bounce effect to notification"""
        try:
            # Quick scale animation
            original_height = self.notif_box.height()
            self.notif_box.setFixedHeight(int(original_height * 1.1))
            QTimer.singleShot(100, lambda: self.notif_box.setFixedHeight(original_height))
        except:
            pass

    def _handle_notification_error(self, error_msg: str):
        """Handle notification processing errors"""
        if self.logger:
            self.logger.error(f"Notification processing error: {error_msg}")
    
    def _on_tts_error(self, error_msg: str):
        """Handle TTS errors"""
        self.logger.error(f"TTS error: {error_msg}")
        # Show error in notification box instead of blocking dialog
        try:
            self.notif_label.setText(f"⚠️ TTS Error: {error_msg[:50]}")
            self.notif_box.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #F59E0B, stop:1 #D97706);
                    border-radius: 21px;
                    padding: 0 6px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }}
                QFrame:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #D97706, stop:1 #B45309);
                    border: 2px solid rgba(255, 255, 255, 0.5);
                }}
            """)
            self.notif_box.show()
            
            # Auto-hide after 5 seconds
            QTimer.singleShot(5000, lambda: self.notif_box.hide())
        except:
            pass

    def _refresh_calc(self):
        if hasattr(self, "calc_view"):
            self.calc_view.refresh_table(force=True)
    
    def _refresh_stock(self):
        if hasattr(self, "stock_view"):
            self.stock_view.refresh_list()

    def _on_row_height_changed(self, height: int):
        """Cập nhật chiều cao row cho tất cả tables"""
        # Calculation view
        if hasattr(self, "calc_view"):
            self.calc_view.table.verticalHeader().setDefaultSectionSize(height)
            if hasattr(self.calc_view, 'prod_table'):
                self.calc_view.prod_table.verticalHeader().setDefaultSectionSize(height)

        # Stock view
        if hasattr(self, "stock_view"):
            self.stock_view.table.verticalHeader().setDefaultSectionSize(height)

        # Product view
        if hasattr(self, "product_view"):
            self.product_view.table.verticalHeader().setDefaultSectionSize(height)

        # History view
        if hasattr(self, "history_view"):
            self.history_view.table.verticalHeader().setDefaultSectionSize(height)

        # Bank view
        if hasattr(self, "bank_view"):
            self.bank_view.table.verticalHeader().setDefaultSectionSize(height)
        
        # Task view
        if hasattr(self, "task_view"):
            self.task_view.table.verticalHeader().setDefaultSectionSize(height)

    def _on_widget_height_changed(self, height: int):
        """Cập nhật chiều cao widget - cần refresh lại views"""
        # Lưu giá trị mới
        if hasattr(self, "calc_view"):
            self.calc_view._widget_height = height
            self.calc_view.refresh_table()
            self.calc_view.refresh_product_list()

        if hasattr(self, "stock_view"):
            self.stock_view._widget_height = height
            self.stock_view.refresh_list()

        if hasattr(self, "product_view"):
            self.product_view._widget_height = height
            self.product_view.refresh_list()

    def _apply_theme(self):
        self.setStyleSheet(AppTheme.get_stylesheet())
    
    def _setup_keyboard_shortcuts(self):
        """Setup global keyboard shortcuts"""
        from PyQt6.QtGui import QShortcut, QKeySequence
        from PyQt6.QtCore import Qt
        
        # Undo: Ctrl+Z
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._on_undo)
        
        # Redo: Ctrl+Y or Ctrl+Shift+Z
        redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        redo_shortcut.activated.connect(self._on_redo)
        
        redo_shortcut2 = QShortcut(QKeySequence("Ctrl+Shift+Z"), self)
        redo_shortcut2.activated.connect(self._on_redo)
        
        # Save: Ctrl+S
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._on_save)
        
        # Refresh: F5
        refresh_shortcut = QShortcut(QKeySequence.StandardKey.Refresh, self)
        refresh_shortcut.activated.connect(self._on_refresh)
        
        # Switch tabs: Ctrl+1/2/3/4/5
        for i in range(5):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i+1}"), self)
            shortcut.activated.connect(lambda idx=i: self._switch_view(idx))
        
        # Close notification: Esc
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self._on_escape)
        
        # Find/Search: Ctrl+F
        find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        find_shortcut.activated.connect(self._on_find)
        
        # New item: Ctrl+N
        new_shortcut = QShortcut(QKeySequence.StandardKey.New, self)
        new_shortcut.activated.connect(self._on_new)
        
        # Quit: Ctrl+Q
        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self.close)
        
        self.logger.info("Keyboard shortcuts initialized")
    
    def _on_escape(self):
        """Handle Escape key - close notifications"""
        if self.notif_box.isVisible():
            self.notif_box.hide()
        if self.task_notif_box.isVisible():
            self.task_notif_box.hide()
    
    def _on_find(self):
        """Handle Ctrl+F - focus search in current view"""
        current_view = self.content_stack.currentWidget()
        
        # Try to find and focus search input in current view
        if hasattr(current_view, 'search_input'):
            current_view.search_input.setFocus()
            current_view.search_input.selectAll()
    
    def _on_new(self):
        """Handle Ctrl+N - add new item in current view"""
        current_idx = self.content_stack.currentIndex()
        
        # Calculation view - add product
        if current_idx == 0 and hasattr(self, 'calculation_view'):
            if hasattr(self.calculation_view, '_add_product'):
                self.calculation_view._add_product()
        
        # Task view - add task
        elif current_idx == 1 and hasattr(self, 'task_view'):
            if hasattr(self.task_view, '_add_task'):
                self.task_view._add_task()
        
        # Product view - add product
        elif current_idx == 3 and hasattr(self, 'product_view'):
            if hasattr(self.product_view, '_add_product'):
                self.product_view._add_product()
        
        # Stock view - add product
        elif current_idx == 4 and hasattr(self, 'stock_view'):
            if hasattr(self.stock_view, '_add_product'):
                self.stock_view._add_product()
    
    def _on_undo(self):
        """Handle Ctrl+Z - Undo"""
        if self.command_history and self.command_history.can_undo():
            try:
                self.command_history.undo()
                self._refresh_all_views()
                
                # Show notification
                desc = self.command_history.get_redo_description()
                if desc:
                    self.notif_label.setText(f"↶ Đã hoàn tác: {desc}")
                    self.notif_box.setStyleSheet(f"""
                        QFrame {{
                            background: {AppColors.PRIMARY};
                            border-radius: 19px;
                            padding: 0 4px;
                        }}
                    """)
                    self.notif_box.show()
                    QTimer.singleShot(2000, lambda: self.notif_box.hide())
            except Exception as e:
                self.logger.error(f"Undo failed: {e}")
    
    def _on_redo(self):
        """Handle Ctrl+Y - Redo"""
        if self.command_history and self.command_history.can_redo():
            try:
                self.command_history.redo()
                self._refresh_all_views()
                
                # Show notification
                desc = self.command_history.get_undo_description()
                if desc:
                    self.notif_label.setText(f"↷ Đã làm lại: {desc}")
                    self.notif_box.setStyleSheet(f"""
                        QFrame {{
                            background: {AppColors.PRIMARY};
                            border-radius: 19px;
                            padding: 0 4px;
                        }}
                    """)
                    self.notif_box.show()
                    QTimer.singleShot(2000, lambda: self.notif_box.hide())
            except Exception as e:
                self.logger.error(f"Redo failed: {e}")
    
    def _on_save(self):
        """Handle Ctrl+S - Quick save/backup"""
        if self.backup_service:
            try:
                backup_file = self.backup_service.create_backup(prefix="manual")
                self.notif_label.setText(f"💾 Đã lưu: {backup_file.name}")
                self.notif_box.setStyleSheet(f"""
                    QFrame {{
                        background: {AppColors.SUCCESS};
                        border-radius: 19px;
                        padding: 0 4px;
                    }}
                """)
                self.notif_box.show()
                QTimer.singleShot(3000, lambda: self.notif_box.hide())
            except Exception as e:
                self.logger.error(f"Manual backup failed: {e}")
    
    def _on_refresh(self):
        """Handle F5 - Refresh all views"""
        self._refresh_all_views()
        self.notif_label.setText("🔄 Đã làm mới")
        self.notif_box.setStyleSheet(f"""
            QFrame {{
                background: {AppColors.PRIMARY};
                border-radius: 19px;
                padding: 0 4px;
            }}
        """)
        self.notif_box.show()
        QTimer.singleShot(1000, lambda: self.notif_box.hide())
    
    def _refresh_all_views(self):
        """Refresh all views"""
        if hasattr(self, 'calc_view'):
            self.calc_view.refresh_table()
        if hasattr(self, 'stock_view'):
            self.stock_view.refresh_list()
        if hasattr(self, 'product_view'):
            self.product_view.refresh_list()
    
    def _check_alerts(self):
        """Check for inventory alerts"""
        if self.alert_service:
            try:
                alerts = self.alert_service.check_all_alerts()
                if alerts:
                    self.logger.info(f"Found {len(alerts)} alerts")
                    # Update alert panel if exists
                    if hasattr(self, 'calc_view') and hasattr(self.calc_view, 'alert_panel'):
                        self.calc_view.alert_panel.update_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Alert check failed: {e}")
    
    def _refresh_alerts(self):
        """Refresh alerts manually"""
        if self.alert_service:
            try:
                alerts = self.alert_service.check_all_alerts()
                if hasattr(self, 'calc_view') and hasattr(self.calc_view, 'alert_panel'):
                    self.calc_view.alert_panel.update_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Alert refresh failed: {e}")
    
    def _on_alert_triggered(self, alert):
        """Handle alert notification"""
        from services.alert_service import AlertLevel
        
        # Show alert in notification box
        if alert.level == AlertLevel.CRITICAL:
            bg_color = "#DC2626"  # Red
        elif alert.level == AlertLevel.WARNING:
            bg_color = AppColors.WARNING
        else:
            bg_color = AppColors.PRIMARY
        
        self.notif_label.setText(f"⚠️ {alert.title}: {alert.message}")
        self.notif_box.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-radius: 19px;
                padding: 0 4px;
            }}
        """)
        self.notif_box.show()
    
    def _check_daily_backup(self):
        """Check and create daily backup if needed"""
        if self.backup_service:
            try:
                backup_file = self.backup_service.auto_backup_daily()
                if backup_file:
                    self.logger.info(f"Daily backup created: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Daily backup failed: {e}")

    def closeEvent(self, event):
        """Handle window close event - cleanup resources"""
        self.logger.info("Application closing - cleaning up resources")
        
        # Create shutdown backup
        if hasattr(self, 'backup_service') and self.backup_service:
            try:
                backup_file = self.backup_service.auto_backup_on_shutdown()
                if backup_file:
                    self.logger.info(f"Shutdown backup created: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Shutdown backup failed: {e}")
        
        # Stop timers
        if hasattr(self, '_alert_timer'):
            self._alert_timer.stop()
        if hasattr(self, '_backup_timer'):
            self._backup_timer.stop()
        
        # Stop TTS
        if hasattr(self, '_tts_service'):
            self._tts_service.stop()
        
        # Stop notification server
        if hasattr(self, 'notif_thread'):
            self.notif_thread.stop()
            self.notif_thread.wait(2000)  # Wait max 2 seconds
        
        # Cleanup views
        if hasattr(self, 'bank_view'):
            self.bank_view.cleanup()
        
        if hasattr(self, 'quick_peek'):
            self.quick_peek.cleanup()
        
        # Cleanup processor
        if hasattr(self, '_notification_processor'):
            try:
                self._notification_processor.notification_processed.disconnect()
                self._notification_processor.error_occurred.disconnect()
            except:
                pass
        
        # Accept the close event
        event.accept()
        self.logger.info("Application closed successfully")


def main():
    import ctypes

    # Performance optimization for Windows
    try:
        myappid = "bangtinh.warehouse.app.2.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # Set process priority to above normal for better responsiveness
        import psutil

        p = psutil.Process()
        p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
    except:
        pass

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Load custom fonts from assets
    from PyQt6.QtGui import QFontDatabase

    fonts_dir = BASE_DIR / "assets" / "fonts"

    # Load Roboto fonts
    roboto_dir = fonts_dir / "Roboto"
    if roboto_dir.exists():
        for font_file in roboto_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))

    # Load Cabin fonts
    cabin_dir = fonts_dir / "Cabin-master" / "fonts" / "TTF"
    if cabin_dir.exists():
        for font_file in cabin_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))

    # Set default application font to Roboto
    app.setFont(QFont("Roboto", 11))
    app.setApplicationVersion(APP_VERSION)

    icon_path = BASE_DIR / "assets" / "icon.png"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            app.setWindowIcon(icon)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Initialize container with configuration
    from PyQt6.QtWidgets import QMessageBox

    from core.config import Config
    from core.container import Container
    from core.license import LicenseManager, LicenseValidator

    config = Config.from_env()

    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        error_msg = "Configuration errors:\n" + "\n".join(config_errors)
        QMessageBox.critical(None, "Configuration Error", error_msg)
        sys.exit(1)

    container = Container(config)
    logger = container.get("logger")

    # Validate license at startup
    try:
        validator = LicenseValidator(logger=logger)
        license_manager = LicenseManager(validator, logger)

        if not license_manager.validate_startup_license(
            config.license_key, config.environment
        ):
            QMessageBox.critical(
                None,
                "License Error",
                "Invalid or expired license key.\n\n"
                "Please contact support to obtain a valid license.",
            )
            logger.error("Application startup blocked: Invalid license")
            sys.exit(1)

        # Store license manager in container for later use
        container.register_singleton("license_manager", license_manager)

    except Exception as e:
        logger.error(f"License validation error: {e}")
        if config.environment == "production":
            QMessageBox.critical(
                None, "License Error", f"Failed to validate license: {str(e)}"
            )
            sys.exit(1)

    # Create main window with injected container
    window = MainWindow(container=container)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
