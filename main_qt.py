"""
Main Application - Phần mềm Quản lý Xuất kho & Dịch vụ
PyQt6 Version - Clean Minimal Design
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from database.connection import init_db
init_db()

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, BASE_DIR
from ui.qt_theme import AppTheme
from ui.qt_views.calculation_view import CalculationView
from ui.qt_views.stock_view import StockView
from ui.qt_views.product_view import ProductView
from ui.qt_views.history_view import HistoryView
from ui.qt_views.settings_view import SettingsView


class MainWindow(QMainWindow):
    """Main window - clean design"""
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._apply_theme()
    
    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        icon_path = BASE_DIR / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - WINDOW_WIDTH) // 2
        y = (screen.height() - WINDOW_HEIGHT) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self._create_views()
        
        self.tabs.addTab(self.calc_view, "Bảng tính")
        self.tabs.addTab(self.stock_view, "Kho hàng")
        self.tabs.addTab(self.product_view, "Sản phẩm")
        self.tabs.addTab(self.history_view, "Lịch sử")
        self.tabs.addTab(self.settings_view, "Cài đặt")
        
        layout.addWidget(self.tabs)
    
    def _create_views(self):
        self.calc_view = CalculationView()
        self.stock_view = StockView(on_refresh_calc=self._refresh_calc)
        self.product_view = ProductView(on_refresh_calc=self._refresh_calc)
        self.history_view = HistoryView()
        self.settings_view = SettingsView()
    
    def _refresh_calc(self):
        if hasattr(self, 'calc_view'):
            self.calc_view.refresh_table()
    
    def _apply_theme(self):
        self.setStyleSheet(AppTheme.get_stylesheet())


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    icon_path = BASE_DIR / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
