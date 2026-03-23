"""
Main Application - Phần mềm Quản lý Xuất kho & Dịch vụ
PyQt6 Version - Modern Premium Design - Refactored
"""

import html
import sys
import time
from pathlib import Path

from PyQt6.QtCore import (QEasingCurve, QEvent, QPropertyAnimation, Qt, QTimer,
                          pyqtSignal)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (QApplication, QFrame, QGraphicsOpacityEffect,
                             QHBoxLayout, QLabel, QMainWindow, QPushButton,
                             QStackedWidget, QTabWidget, QVBoxLayout, QWidget)

from ..core.constants import (APP_NAME, APP_VERSION, WINDOW_HEIGHT,
                              WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_WIDTH)
from .theme import AppColors, AppTheme
from ..core.paths import ASSETS

# Import network components
from ..network.notification_server import NotificationServer
from ..network.discovery_server import DiscoveryServer
from ..network.network_monitor import NetworkMonitor, get_best_ip
from ..network.connection_heartbeat import ConnectionHeartbeat
# Import views
from .views.calculation_view import CalculationView
from .views.calculator_tool_view import CalculatorToolView
from .views.history_view import HistoryView
from .views.product_view import ProductView
from .views.settings_view import SettingsView
from .views.stock_view import StockView
from .views.task_view import TaskView
from .views.bank_view import BankView
from .widgets.quick_bank_peek import QuickBankPeek
from .widgets.status_indicator import StatusIndicator
from ..workers.notification_processor import NotificationProcessor

# BankView, NotificationHandler, NotificationServer, QuickBankPeek
# have been moved to separate files for better organization


class MainWindow(QMainWindow):
    """Main window - modern premium design"""

    # Signal for cross-thread notification
    notification_received = pyqtSignal(str)

    def __init__(self, container=None):
        super().__init__()
        # Inject dependency container
        from ..core.config import Config
        from ..core.container import Container

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
        self._notification_processor.notification_processed.connect(
            self._handle_processed_notification
        )
        self._notification_processor.error_occurred.connect(
            self._handle_notification_error
        )

        # Initialize TTS service
        from ..services.tts_service import TTSService

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
        self._setup_keyboard_shortcuts()

        # Start notification server
        self._start_notification_server()

        # Start network monitor + heartbeat
        self._start_network_monitor()
        self._start_heartbeat()

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

        # Timer for status indicator polling (every 10 seconds)
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._poll_server_status)
        self._status_timer.start(10000)  # 10 seconds

        # Track last notification time for health monitoring
        self._last_notification_at = None

        # Create startup backup (deferred 3s so window shows first)
        if self.backup_service:
            QTimer.singleShot(3000, self._do_startup_backup)

    def _do_startup_backup(self):
        """Run startup backup after window is shown (non-blocking startup)"""
        if self.backup_service:
            try:
                backup_file = self.backup_service.auto_backup_on_startup()
                if backup_file:
                    self.logger.info(f"Startup backup created: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Startup backup failed: {e}")

    def _setup_animations_internal(self):
        """Setup animations for UI elements - called internally after content_stack is ready.

        The opacity effect is applied *per page* (not on the whole stack)
        so the outgoing page stays fully opaque while the incoming one
        fades in.  This eliminates the "ghosting" artefact where old
        content was visible through the semi-transparent stack widget.
        """
        self._page_effects: dict[int, QGraphicsOpacityEffect] = {}

        for i in range(self.content_stack.count()):
            page = self.content_stack.widget(i)
            effect = QGraphicsOpacityEffect(page)
            effect.setOpacity(1.0)
            page.setGraphicsEffect(effect)
            self._page_effects[i] = effect

        # Reusable animation — target is reassigned in _switch_view
        self.fade_animation = QPropertyAnimation()
        self.fade_animation.setDuration(110)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _setup_window(self):
        self.setWindowTitle(APP_NAME)
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
        self.sidebar.setFixedWidth(180)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet("""
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:0.3 #0f172a, stop:1 #020617);
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(14, 20, 14, 16)
        sidebar_layout.setSpacing(4)

        # Logo with subtle glass-morphism badge
        logo_frame = QFrame()
        logo_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(16, 185, 129, 0.15), stop:1 rgba(59, 130, 246, 0.1));
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
        """)
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(12, 10, 12, 10)
        logo_layout.setSpacing(2)
        logo = QLabel("WMS")
        logo.setStyleSheet("""
            color: white; 
            font-weight: 950; 
            font-size: 18px; 
            letter-spacing: 4px;
            background: transparent;
            border: none;
        """)
        logo_sub = QLabel("Warehouse System")
        logo_sub.setStyleSheet("""
            color: rgba(148, 163, 184, 0.8);
            font-size: 9px;
            font-weight: 600;
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
        """)
        logo_layout.addWidget(logo)
        logo_layout.addWidget(logo_sub)
        sidebar_layout.addWidget(logo_frame)
        sidebar_layout.addSpacing(16)

        self.nav_btns = []
        self._add_nav_btn(sidebar_layout, "Quản lý", 0)
        self._add_nav_btn(sidebar_layout, "Ghi chú", 1)
        self._add_nav_btn(sidebar_layout, "Bank", 2)
        self._add_nav_btn(sidebar_layout, "Lịch sử", 3)
        self._add_nav_btn(sidebar_layout, "Cài đặt", 4)
        self._add_nav_btn(sidebar_layout, "Máy tính", 5)

        sidebar_layout.addStretch()

        # Status indicator - shows server state
        self.status_indicator = StatusIndicator()
        self.status_indicator.mousePressEvent = lambda e: self._switch_view(
            4
        )  # Click → Settings
        sidebar_layout.addWidget(self.status_indicator)

        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"""
            color: rgba(148, 163, 184, 0.6); 
            font-size: 10px; 
            padding: 10px 14px;
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
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                padding: 12px 28px;
                font-weight: 600;
                font-size: 13px;
                background: transparent;
                color: {AppColors.TEXT_SECONDARY};
                border-bottom: 2px solid transparent;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                color: {AppColors.PRIMARY};
                border-bottom: 2px solid {AppColors.PRIMARY};
                background: rgba(16, 185, 129, 0.04);
            }}
            QTabBar::tab:hover:!selected {{
                color: {AppColors.TEXT};
                background: rgba(15, 23, 42, 0.03);
                border-bottom: 2px solid {AppColors.BORDER};
            }}
        """)

        self.management_tabs.addTab(self.calc_view, "Tính tiền")

        # Create product list tab from calc_view's prod_tab
        self.product_list_tab = self.calc_view.prod_tab
        self.management_tabs.addTab(self.product_list_tab, "Danh sách SP")

        self.management_tabs.addTab(self.stock_view, "Kho hàng")
        self.management_tabs.addTab(self.product_view, "Sản phẩm")

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

        # Global Header - Clean with subtle bottom shadow
        header = QFrame()
        header.setMinimumHeight(52)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #FAFBFC);
                border-bottom: 1px solid {AppColors.BORDER};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)

        self.breadcrumb = QLabel("Trang chủ / Bảng tính")
        self.breadcrumb.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY}; 
            font-weight: 600; 
            font-size: 12px;
            letter-spacing: 0.3px;
        """)
        header_layout.addWidget(self.breadcrumb)

        header_layout.addStretch()

        # Notification Area
        from .widgets.notification_banners import (BankNotificationBanner,
                                                     SystemNotificationBanner)

        self.notif_banner = BankNotificationBanner()
        self.notif_banner.clicked.connect(
            lambda: self._switch_view(2)
        )  # Cmd 2: Bank View
        self.notif_banner.installEventFilter(self)  # Enable hover → QuickBankPeek
        header_layout.addWidget(self.notif_banner)

        content_layout.addWidget(header)

        content_layout.addWidget(self.content_stack)

        # Bottom Ticker Bar — system/task/Android notifications
        self.task_banner = SystemNotificationBanner()
        self.task_banner.clicked.connect(
            lambda: self._switch_view(1)
        )  # Cmd 1: Task View
        content_layout.addWidget(self.task_banner)

        # Add main_content to main_layout
        main_layout.addWidget(main_content)

        # Setup animations after content_stack is fully initialized
        self._setup_animations_internal()

        # Task Banner init hidden by default

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
        # Update to verify notification banner hover
        if hasattr(self, "notif_banner") and source == self.notif_banner:
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
        pos = self.notif_banner.mapToGlobal(self.notif_banner.rect().bottomLeft())
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

    def _switch_view(self, index):
        """Switch view instantly with a subtle fade-in effect (no delay)"""
        if self.content_stack.currentIndex() == index:
            return

        # Switch page and update UI immediately
        self.content_stack.setCurrentIndex(index)
        names = ["Quản lý", "Ghi chú", "Bank", "Lịch sử", "Cài đặt", "Máy tính"]
        self.breadcrumb.setText(f"Trang chủ / {names[index]}")

        # Update nav buttons
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Subtle fade-in on the new page only (per-page effect, no ghosting)
        try:
            if hasattr(self, "fade_animation") and hasattr(self, "_page_effects"):
                self.fade_animation.stop()
                effect = self._page_effects.get(index)
                if effect:
                    self.fade_animation.setTargetObject(effect)
                    self.fade_animation.setPropertyName(b"opacity")
                    self.fade_animation.start()
        except Exception:
            pass  # Animation not critical

        # Give calculator keyboard focus when switching to it
        if index == 5 and hasattr(self, "calculator_view"):
            QTimer.singleShot(50, self.calculator_view.setFocus)

    def _switch_view_direct(self, index):
        """Switch view directly without animation (fallback)"""
        self.content_stack.setCurrentIndex(index)
        names = ["Quản lý", "Ghi chú", "Bank", "Lịch sử", "Cài đặt", "Máy tính"]
        self.breadcrumb.setText(f"Trang chủ / {names[index]}")
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _create_views(self):
        # Initialize error handler
        from ..utils.error_handler import ErrorHandler

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
        """Refresh stock list in calculation view and stock view"""
        if hasattr(self, "calc_view"):
            # Correct method name is refresh_product_list
            self.calc_view.refresh_product_list()
        
        # Also refresh stock view if it exists to keep in sync
        if hasattr(self, "stock_view"):
            self.stock_view.refresh_list()

    def _start_notification_server(self):
        """Khởi chạy server ngầm để nhận thông báo"""
        # Get config early so it's available for DiscoveryServer below
        config = self.container.get("config")

        # Get notification service from container
        notification_service = self.container.get("notification")
        if notification_service:
            notification_service.register_handler(self._process_notification)
            notification_service.start_server()
            self.logger.info("Notification server started successfully")
        else:
            # Fallback to direct implementation
            http_port = config.notification_port if config else 5005
            if config:
                self.notif_thread = NotificationServer(
                    host=config.notification_host,
                    port=http_port,
                    logger=self.logger,
                    container=self.container,
                )
            else:
                self.notif_thread = NotificationServer(
                    logger=self.logger, container=self.container
                )
            self.notif_thread.msg_received.connect(self._process_notification)
            self.notif_thread.start()

        # Start UDP discovery server (fallback: Android finds PC without knowing IP)
        self._discovery_thread = DiscoveryServer(
            http_port=config.notification_port if config else 5005,
            logger=self.logger,
            container=self.container,
        )
        self._discovery_thread.start()

        # Track discovery for heartbeat
        self._discovery_thread.client_discovered.connect(self._on_device_discovered)

    def _start_network_monitor(self):
        """Start background network monitor for auto-retry on connection loss."""
        server_port = 5005
        config = self.container.get("config")
        if config:
            server_port = config.notification_port

        self._network_monitor = NetworkMonitor(
            check_interval=5.0,
            server_port=server_port,
            logger=self.logger,
        )
        self._network_monitor.network_changed.connect(self._on_network_changed)
        self._network_monitor.server_down.connect(self._on_server_down)
        self._network_monitor.network_lost.connect(self._on_network_lost)
        self._network_monitor.network_restored.connect(self._on_network_restored)
        self._network_monitor.start()

        # Set initial connection type
        best_ip, best_type = get_best_ip()
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_connection_type(best_type)

    def _start_heartbeat(self):
        """Start heartbeat service for tracking Android devices."""
        secret_key = ""
        config = self.container.get("config")
        if config:
            secret_key = config.secret_key

        self._heartbeat = ConnectionHeartbeat(
            ping_interval=15.0,
            server_port=config.notification_port if config else 5005,
            secret_key=secret_key,
            logger=self.logger,
        )
        self._heartbeat.device_online.connect(self._on_heartbeat_device_online)
        self._heartbeat.device_offline.connect(self._on_heartbeat_device_offline)
        self._heartbeat.status_update.connect(self._on_heartbeat_status)
        self._heartbeat.start()

    # ── Network event handlers ──────────────────────────────────

    def _on_device_discovered(self, ip: str):
        """When UDP discovery finds an Android device, track it for heartbeat."""
        if hasattr(self, "_heartbeat"):
            self._heartbeat.add_device(ip)

    def _on_network_changed(self, info: dict):
        """Network interfaces changed (e.g. switched WiFi → Ethernet)."""
        best_type = info.get("best_type", "")
        best_ip = info.get("best_ip", "")
        self.logger.info(f"Network changed: {best_ip} ({best_type})")
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_connection_type(best_type)

    def _on_server_down(self):
        """Notification server port is unreachable — attempt restart."""
        self.logger.warning("Server appears down — attempting auto-restart...")
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_state(StatusIndicator.STATE_RECONNECTING)
        # Attempt restart on main thread via single-shot timer
        QTimer.singleShot(1000, self._restart_notification_server)

    def _on_network_lost(self):
        """All network interfaces lost."""
        self.logger.warning("All network interfaces lost!")
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_state(StatusIndicator.STATE_NO_NETWORK)
            self.status_indicator.set_connection_type("")

    def _on_network_restored(self, best_ip: str):
        """Network came back — restart servers."""
        self.logger.info(f"Network restored ({best_ip}) — restarting servers...")
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_state(StatusIndicator.STATE_RECONNECTING)
        QTimer.singleShot(2000, self._restart_notification_server)

    def _on_heartbeat_device_online(self, ip: str, latency: float):
        self.logger.info(f"Device online: {ip} ({latency:.0f}ms)")

    def _on_heartbeat_device_offline(self, ip: str):
        self.logger.warning(f"Device offline: {ip}")

    def _on_heartbeat_status(self, status: dict):
        """Update device count in status indicator."""
        if hasattr(self, "status_indicator"):
            self.status_indicator.set_device_count(status.get("online_count", 0))

    def _restart_notification_server(self):
        """Stop and restart notification + discovery servers."""
        self.logger.info("Restarting notification infrastructure...")
        try:
            # Stop existing servers
            notification_service = self.container.get("notification")
            if notification_service and hasattr(notification_service, "stop_server"):
                try:
                    notification_service.stop_server()
                except Exception:
                    pass

            if hasattr(self, "notif_thread"):
                try:
                    self.notif_thread.stop()
                    self.notif_thread.wait(2000)
                except Exception:
                    pass

            if hasattr(self, "_discovery_thread"):
                try:
                    self._discovery_thread.stop()
                    self._discovery_thread.wait(2000)
                except Exception:
                    pass

            # Re-start
            self._start_notification_server()
            self.logger.info("Notification infrastructure restarted successfully")
        except Exception as e:
            self.logger.error(f"Failed to restart notification server: {e}")
            if hasattr(self, "status_indicator"):
                self.status_indicator.set_state(StatusIndicator.STATE_STOPPED)

    def _process_notification(self, message):
        """Process notification using worker"""
        self._notification_processor.process_notification(message)

    def _handle_processed_notification(self, data: dict):
        """Handle processed notification data from worker"""
        # Handle special commands first (Ping success, Session update etc)
        # to avoid KeyError when accessing fields like amount or has_amount
        if data.get("has_command"):
            timestamp = data.get("timestamp", "")
            cmd = data.get("command")

            # Change notif_box color to INFO (Emerald Dark or Blue) for system/command events
            if cmd == "PING_SUCCESS":
                # Show test-connection result in the bottom ticker bar
                if hasattr(self, "bank_view"):
                    self.bank_view.add_system_log(f"{data['content']}")
                self.task_banner.show_message(
                    f"📱 {data['content']}", duration=4000
                )
                return

            # Use task notification area for system messages
            content = f"{data['content']}"
            self.task_banner.show_message(content, duration=5000)

            if cmd == "REFRESH_SESSION":
                self._refresh_calc()

            return

        # Update UI with processed data for normal notifications
        timestamp = data.get("timestamp", "")
        source = data.get("source", "")
        amount = data.get("amount", "")
        sender_name = data.get("sender_name", "")
        content = data.get("content", "")
        has_amount = data.get("has_amount", False)

        # Record notification for health monitoring
        self._last_notification_at = int(time.time() * 1000)
        if hasattr(self, "status_indicator"):
            self.status_indicator.record_notification()

        if has_amount:
            safe_sender = html.escape(sender_name[:30]) if sender_name else ""
            safe_source = html.escape(source)
            safe_amount = html.escape(amount)

            if safe_sender:
                rich_text = f"<span style='font-size:13px; color:white;'>{timestamp} | <b>{safe_amount}</b> | {safe_sender}</span>"
            else:
                rich_text = f"<span style='font-size:13px; color:white;'>{timestamp} | <b>{safe_amount}</b> | {safe_source}</span>"

            # Show banner (Bank notifications stay until closed or replaced)
            self.notif_banner.show_message(rich_text)

            # Speak notification using TTS
            if self._tts_service and amount:
                self._tts_service.speak_transaction(amount, sender_name)

        if hasattr(self, "bank_view"):
            # Always add to raw logs
            self.bank_view.add_raw_log(timestamp, source, content)

            # Only add to transactions if it has amount
            if has_amount:
                self.bank_view.add_notif(
                    timestamp, source, amount, sender_name, content
                )
        else:
            if self.logger:
                self.logger.warning(
                    "bank_view not initialized yet, notification not saved"
                )

    def _handle_notification_error(self, error_msg: str):
        """Handle notification processing errors"""
        if self.logger:
            self.logger.error(f"Notification processing error: {error_msg}")

    def _on_tts_error(self, error_msg: str):
        """Handle TTS errors"""
        self.logger.error(f"TTS error: {error_msg}")
        # Show error in task banner
        try:
            self.task_banner.show_message(
                f"TTS Error: {error_msg[:50]}", duration=5000
            )
        except:
            pass

    def _refresh_calc(self):
        if hasattr(self, "calc_view"):
            self.calc_view.refresh_table(force=True)

    def _on_row_height_changed(self, height: int):
        """Cập nhật chiều cao row cho tất cả tables"""
        # Calculation view
        if hasattr(self, "calc_view"):
            self.calc_view.table.verticalHeader().setDefaultSectionSize(height)
            if hasattr(self.calc_view, "prod_table"):
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
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QKeySequence, QShortcut

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
        if hasattr(self, "notif_banner") and self.notif_banner.isVisible():
            self.notif_banner.hide_banner()
        if hasattr(self, "task_banner") and self.task_banner.isVisible():
            self.task_banner.hide_banner()

    def _on_find(self):
        """Handle Ctrl+F - focus search in current view"""
        current_view = self.content_stack.currentWidget()

        # Try to find and focus search input in current view
        if hasattr(current_view, "search_input"):
            current_view.search_input.setFocus()
            current_view.search_input.selectAll()

    def _on_new(self):
        """Handle Ctrl+N - add new item in current view"""
        current_idx = self.content_stack.currentIndex()

        # Management view - check which tab is active
        if current_idx == 0:
            tab_idx = self.management_tabs.currentIndex()
            # Calculation or Product List Tab
            if tab_idx in [0, 1] and hasattr(self, "calc_view"):
                if hasattr(self.calc_view, "_add_product"):
                    self.calc_view._add_product()
            # Quick Price / Product View Tab
            elif tab_idx == 3 and hasattr(self, "product_view"):
                if hasattr(self.product_view, "_add_quick_price"):
                    self.product_view._add_quick_price()

        # Task view - add task
        elif current_idx == 1 and hasattr(self, "task_view"):
            if hasattr(self.task_view, "_add_task"):
                self.task_view._add_task()

    def _on_undo(self):
        """Handle Ctrl+Z - Undo"""
        if self.command_history and self.command_history.can_undo():
            try:
                self.command_history.undo()
                self._refresh_all_views()

                desc = self.command_history.get_redo_description()
                if desc:
                    self.task_banner.show_message(
                        f"Đã hoàn tác: {desc}", duration=2000
                    )
            except Exception as e:
                self.logger.error(f"Undo failed: {e}")

    def _on_redo(self):
        """Handle Ctrl+Y - Redo"""
        if self.command_history and self.command_history.can_redo():
            try:
                self.command_history.redo()
                self._refresh_all_views()

                desc = self.command_history.get_undo_description()
                if desc:
                    self.task_banner.show_message(
                        f"Đã làm lại: {desc}", duration=2000
                    )
            except Exception as e:
                self.logger.error(f"Redo failed: {e}")

    def _on_save(self):
        """Handle Ctrl+S - Quick save/backup"""
        if self.backup_service:
            try:
                backup_file = self.backup_service.create_backup(prefix="manual")
                self.task_banner.show_message(
                    f"Đã lưu: {backup_file.name}", duration=3000
                )
            except Exception as e:
                self.logger.error(f"Manual backup failed: {e}")

    def _on_refresh(self):
        """Handle F5 - Refresh all views"""
        self._refresh_all_views()
        self.task_banner.show_message("Đã làm mới", duration=1000)

    def _refresh_all_views(self):
        """Refresh all views"""
        if hasattr(self, "calc_view"):
            self.calc_view.refresh_table()
        if hasattr(self, "stock_view"):
            self.stock_view.refresh_list()
        if hasattr(self, "product_view"):
            self.product_view.refresh_list()

    def _check_alerts(self):
        """Check for inventory alerts"""
        if self.alert_service:
            try:
                alerts = self.alert_service.check_all_alerts()
                if alerts:
                    self.logger.info(f"Found {len(alerts)} alerts")
                    # Update alert panel if exists
                    if hasattr(self, "calc_view") and hasattr(
                        self.calc_view, "alert_panel"
                    ):
                        self.calc_view.alert_panel.update_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Alert check failed: {e}")

    def _refresh_alerts(self):
        """Refresh alerts manually"""
        if self.alert_service:
            try:
                alerts = self.alert_service.check_all_alerts()
                if hasattr(self, "calc_view") and hasattr(
                    self.calc_view, "alert_panel"
                ):
                    self.calc_view.alert_panel.update_alerts(alerts)
            except Exception as e:
                self.logger.error(f"Alert refresh failed: {e}")

    def _on_alert_triggered(self, alert):
        """Handle alert notification"""
        self.task_banner.show_message(f"{alert.title}: {alert.message}")

    def _check_daily_backup(self):
        """Check and create daily backup if needed"""
        if self.backup_service:
            try:
                backup_file = self.backup_service.auto_backup_daily()
                if backup_file:
                    self.logger.info(f"Daily backup created: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Daily backup failed: {e}")

    def _poll_server_status(self):
        """Poll notification server state and update status indicator"""
        if not hasattr(self, "status_indicator"):
            return

        try:
            # Check if notification service is running
            notification_service = self.container.get("notification")
            if notification_service and hasattr(notification_service, "is_running"):
                if notification_service.is_running():
                    # Server is running — check for no-data timeout
                    self.status_indicator.check_no_data()
                    if self.status_indicator._state != StatusIndicator.STATE_NO_DATA:
                        self.status_indicator.set_state(StatusIndicator.STATE_RUNNING)
                else:
                    self.status_indicator.set_state(StatusIndicator.STATE_STOPPED)
            elif hasattr(self, "notif_thread"):
                # Fallback: check thread-based server
                if self.notif_thread.isRunning():
                    self.status_indicator.check_no_data()
                    if self.status_indicator._state != StatusIndicator.STATE_NO_DATA:
                        self.status_indicator.set_state(StatusIndicator.STATE_RUNNING)
                else:
                    self.status_indicator.set_state(StatusIndicator.STATE_STOPPED)
            else:
                self.status_indicator.set_state(StatusIndicator.STATE_STOPPED)
        except Exception as e:
            self.logger.debug(f"Status poll error: {e}")
            self.status_indicator.set_state(StatusIndicator.STATE_STOPPED)

    def closeEvent(self, event):
        """Handle window close event - cleanup resources"""
        self.logger.info("Application closing - cleaning up resources")

        # Create shutdown backup
        if hasattr(self, "backup_service") and self.backup_service:
            try:
                backup_file = self.backup_service.auto_backup_on_shutdown()
                if backup_file:
                    self.logger.info(f"Shutdown backup created: {backup_file.name}")
            except Exception as e:
                self.logger.error(f"Shutdown backup failed: {e}")

        # Stop timers
        if hasattr(self, "_alert_timer"):
            self._alert_timer.stop()
        if hasattr(self, "_backup_timer"):
            self._backup_timer.stop()
        if hasattr(self, "_status_timer"):
            self._status_timer.stop()

        # Stop network monitor + heartbeat
        if hasattr(self, "_network_monitor"):
            self._network_monitor.stop()
            self._network_monitor.wait(2000)
        if hasattr(self, "_heartbeat"):
            self._heartbeat.stop()
            self._heartbeat.wait(2000)

        # Stop discovery server
        if hasattr(self, "_discovery_thread"):
            self._discovery_thread.stop()
            self._discovery_thread.wait(2000)

        # Stop TTS
        if hasattr(self, "_tts_service"):
            self._tts_service.stop()

        # Stop ngrok/cloudflare tunnel (if running via settings_view)
        if hasattr(self, "settings_view") and hasattr(self.settings_view, "_tunnel_service"):
            svc = self.settings_view._tunnel_service
            if svc and svc.is_running:
                svc.stop()
                self.logger.info("Tunnel stopped")

        # Stop notification server
        if hasattr(self, "notif_thread"):
            self.notif_thread.stop()
            self.notif_thread.wait(2000)  # Wait max 2 seconds

        # Cleanup views
        if hasattr(self, "bank_view"):
            self.bank_view.cleanup()

        if hasattr(self, "quick_peek"):
            self.quick_peek.cleanup()

        # Cleanup processor
        if hasattr(self, "_notification_processor"):
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
    from ..core.paths import ASSETS

    fonts_dir = ASSETS / "fonts"

    # Load Roboto fonts
    roboto_dir = fonts_dir / "Roboto"
    if roboto_dir.exists():
        for font_file in roboto_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                print(f"Failed to load font: {font_file}")

    # Load Cabin fonts
    cabin_dir = fonts_dir / "Cabin-master" / "fonts" / "TTF"
    if cabin_dir.exists():
        for font_file in cabin_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id == -1:
                print(f"Failed to load font: {font_file}")

    # Set default application font to Roboto
    app.setFont(QFont("Roboto", 11))
    app.setApplicationVersion(APP_VERSION)

    # Load app icon
    icon_path = ASSETS / "icons" / "icon.png"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            app.setWindowIcon(icon)

    # Initialize container with configuration
    from PyQt6.QtWidgets import QMessageBox

    from ..core.config import Config
    from ..core.container import Container
    config = Config.from_env()

    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        error_msg = "Configuration errors:\n" + "\n".join(config_errors)
        QMessageBox.critical(None, "Configuration Error", error_msg)
        sys.exit(1)

    container = Container(config)
    logger = container.get("logger")

    # Create main window with injected container
    window = MainWindow(container=container)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
