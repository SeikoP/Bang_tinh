"""
Main Window - Refactored
Split from monolithic app_window.py
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget
)

from core.container import Container
from ui.theme import AppTheme
from ui.views.calculation_view import CalculationView
from ui.views.stock_view import StockView
from ui.views.product_view import ProductView
from ui.views.bank_view import BankView
from ui.views.history_view import HistoryView
from ui.views.settings_view import SettingsView
from ui.widgets.notification_toast import NotificationToast


class MainWindow(QMainWindow):
    """
    Main application window
    
    Responsibilities:
    - Window setup
    - Navigation
    - View management
    - Global UI state
    
    Does NOT handle:
    - Business logic (use services)
    - Data access (use repositories)
    - Network (use network layer)
    """
    
    # Signals
    notification_received = pyqtSignal(str)
    
    def __init__(self, container: Container):
        super().__init__()
        
        # Dependencies
        self.container = container
        self.logger = container.get("logger")
        self.config = container.get("config")
        
        # UI components
        self.sidebar = None
        self.content_stack = None
        self.nav_btns = []
        self.views = {}
        self.notification_toast = None
        
        # Setup
        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._connect_signals()
    
    def _setup_window(self):
        """Setup window properties"""
        self.setWindowTitle(f"{self.config.app_name} v{self.config.app_version}")
        self.resize(self.config.window_width, self.config.window_height)
        self.setMinimumSize(850, 600)
        
        # Set icon
        try:
            from app.core.paths import ASSETS
            icon_path = ASSETS / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            self.logger.warning(f"Could not load icon: {e}")
        
        # Center window
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.config.window_width) // 2
        y = (screen.height() - self.config.window_height) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        """Setup UI components"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_widget = self._create_content_area()
        main_layout.addWidget(content_widget)
        
        # Notification toast
        self.notification_toast = NotificationToast(self)
    
    def _create_sidebar(self) -> QFrame:
        """Create navigation sidebar"""
        sidebar = QFrame()
        sidebar.setFixedWidth(150)
        sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 24, 12, 24)
        layout.setSpacing(8)
        
        # Logo
        logo = QLabel("BANGLA")
        logo.setObjectName("logo")
        layout.addWidget(logo)
        
        # Navigation buttons
        nav_items = [
            ("🧮 Bảng tính", "calculation"),
            ("📦 Kho hàng", "stock"),
            ("🏷️ Sản phẩm", "product"),
            ("🏦 Ngân hàng", "bank"),
            ("📜 Lịch sử", "history"),
            ("⚙️ Cài đặt", "settings"),
        ]
        
        for label, view_name in nav_items:
            btn = self._create_nav_button(label, view_name)
            self.nav_btns.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Version
        version = QLabel(f"v{self.config.app_version}")
        version.setObjectName("version")
        layout.addWidget(version)
        
        return sidebar
    
    def _create_nav_button(self, label: str, view_name: str) -> QPushButton:
        """Create navigation button"""
        btn = QPushButton(label)
        btn.setObjectName("nav_button")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_view(view_name))
        return btn
    
    def _create_content_area(self) -> QWidget:
        """Create content area with views"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Content stack
        self.content_stack = QStackedWidget()
        self._create_views()
        layout.addWidget(self.content_stack)
        
        return container
    
    def _create_header(self) -> QFrame:
        """Create global header"""
        header = QFrame()
        header.setFixedHeight(64)
        header.setObjectName("header")
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)
        
        # Breadcrumb
        self.breadcrumb = QLabel("Trang chủ > Bảng tính")
        self.breadcrumb.setObjectName("breadcrumb")
        layout.addWidget(self.breadcrumb)
        
        layout.addStretch()
        
        # User info / actions
        # TODO: Add user menu, notifications, etc.
        
        return header
    
    def _create_views(self):
        """Create all views"""
        # Calculation view
        calc_view = CalculationView(self.container)
        self.views["calculation"] = calc_view
        self.content_stack.addWidget(calc_view)
        
        # Stock view
        stock_view = StockView(self.container)
        self.views["stock"] = stock_view
        self.content_stack.addWidget(stock_view)
        
        # Product view
        product_view = ProductView(self.container)
        self.views["product"] = product_view
        self.content_stack.addWidget(product_view)
        
        # Bank view
        bank_view = BankView(self.container)
        self.views["bank"] = bank_view
        self.content_stack.addWidget(bank_view)
        
        # History view
        history_view = HistoryView(self.container)
        self.views["history"] = history_view
        self.content_stack.addWidget(history_view)
        
        # Settings view
        settings_view = SettingsView(self.container)
        self.views["settings"] = settings_view
        self.content_stack.addWidget(settings_view)
    
    def _apply_theme(self):
        """Apply application theme"""
        theme = AppTheme()
        self.setStyleSheet(theme.get_stylesheet())
    
    def _connect_signals(self):
        """Connect signals"""
        # Connect notification signal to bank view
        if "bank" in self.views:
            self.notification_received.connect(
                self.views["bank"].handle_notification
            )
    
    def _switch_view(self, view_name: str):
        """Switch to view"""
        if view_name in self.views:
            view = self.views[view_name]
            self.content_stack.setCurrentWidget(view)
            
            # Update breadcrumb
            breadcrumbs = {
                "calculation": "Trang chủ > Bảng tính",
                "stock": "Trang chủ > Kho hàng",
                "product": "Trang chủ > Sản phẩm",
                "bank": "Trang chủ > Ngân hàng",
                "history": "Trang chủ > Lịch sử",
                "settings": "Trang chủ > Cài đặt",
            }
            self.breadcrumb.setText(breadcrumbs.get(view_name, "Trang chủ"))
            
            # Update nav button states
            for i, btn in enumerate(self.nav_btns):
                btn.setProperty("active", i == list(self.views.keys()).index(view_name))
                btn.style().unpolish(btn)
                btn.style().polish(btn)
    
    def show_notification(self, message: str, type: str = "info"):
        """Show notification toast"""
        if self.notification_toast:
            self.notification_toast.show_message(message, type)
    
    def closeEvent(self, event):
        """Handle window close"""
        # TODO: Confirm close if unsaved changes
        # TODO: Stop background workers
        # TODO: Close network connections
        
        self.logger.info("Application closing")
        event.accept()
