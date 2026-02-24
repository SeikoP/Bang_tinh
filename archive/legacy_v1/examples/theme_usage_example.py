"""
Example: How to use the new theme system
"""

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from ui.theme import AppTheme
from ui.widgets.data_table import DataTable
from ui.widgets.loading_spinner import LoadingOverlay
from ui.widgets.notification_toast import NotificationToast


class ExampleWindow(QMainWindow):
    """Example window showing theme usage"""
    
    def __init__(self):
        super().__init__()
        
        # Apply theme
        theme = AppTheme()
        self.setStyleSheet(theme.get_stylesheet())
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(theme.layout.spacing_medium)
        layout.setContentsMargins(
            theme.layout.spacing_large,
            theme.layout.spacing_large,
            theme.layout.spacing_large,
            theme.layout.spacing_large
        )
        
        # ========================================
        # 1. LABELS WITH THEME
        # ========================================
        
        # Title
        title = QLabel("Tiêu đề chính")
        title.setObjectName("title")  # Uses theme styling
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Tiêu đề phụ")
        subtitle.setObjectName("subtitle")
        layout.addWidget(subtitle)
        
        # Section header
        section = QLabel("Phần nội dung")
        section.setObjectName("section_header")
        layout.addWidget(section)
        
        # Hint text
        hint = QLabel("Gợi ý cho người dùng")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        
        # ========================================
        # 2. BUTTONS WITH THEME
        # ========================================
        
        # Primary button (default)
        btn_primary = QPushButton("Primary Button")
        layout.addWidget(btn_primary)
        
        # Secondary button
        btn_secondary = QPushButton("Secondary Button")
        btn_secondary.setObjectName("secondary")
        layout.addWidget(btn_secondary)
        
        # Danger button
        btn_danger = QPushButton("Danger Button")
        btn_danger.setObjectName("danger")
        layout.addWidget(btn_danger)
        
        # Success button
        btn_success = QPushButton("Success Button")
        btn_success.setObjectName("success")
        layout.addWidget(btn_success)
        
        # ========================================
        # 3. DATA TABLE
        # ========================================
        
        table = DataTable(
            headers=["ID", "Tên sản phẩm", "Giá", "Số lượng"],
            row_height=45
        )
        
        # Set column widths
        table.set_column_widths([60, 0, 120, 100])  # 0 = stretch
        
        # Add row actions
        table.add_row_action("edit", "✏️", self._on_edit)
        table.add_row_action("delete", "🗑️", self._on_delete)
        
        # Set data
        data = [
            ["1", "Sản phẩm A", "100,000", "50"],
            ["2", "Sản phẩm B", "200,000", "30"],
            ["3", "Sản phẩm C", "150,000", "20"],
        ]
        table.set_data(data)
        
        layout.addWidget(table)
        
        # ========================================
        # 4. LOADING OVERLAY
        # ========================================
        
        self.loading_overlay = LoadingOverlay(self)
        
        btn_loading = QPushButton("Show Loading")
        btn_loading.clicked.connect(self._show_loading)
        layout.addWidget(btn_loading)
        
        # ========================================
        # 5. TOAST NOTIFICATIONS
        # ========================================
        
        self.toast = NotificationToast(self)
        
        btn_toast_success = QPushButton("Toast Success")
        btn_toast_success.clicked.connect(
            lambda: self.toast.show_message("Thành công!", type="success")
        )
        layout.addWidget(btn_toast_success)
        
        btn_toast_error = QPushButton("Toast Error")
        btn_toast_error.clicked.connect(
            lambda: self.toast.show_message("Có lỗi xảy ra!", type="error")
        )
        layout.addWidget(btn_toast_error)
        
        btn_toast_warning = QPushButton("Toast Warning")
        btn_toast_warning.clicked.connect(
            lambda: self.toast.show_message("Cảnh báo!", type="warning")
        )
        layout.addWidget(btn_toast_warning)
        
        btn_toast_info = QPushButton("Toast Info")
        btn_toast_info.clicked.connect(
            lambda: self.toast.show_message("Thông tin", type="info")
        )
        layout.addWidget(btn_toast_info)
    
    def _show_loading(self):
        """Show loading overlay"""
        self.loading_overlay.show_loading("Đang xử lý...")
        
        # Simulate work
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, self.loading_overlay.hide_loading)
    
    def _on_edit(self, row_idx: int):
        """Handle edit action"""
        self.toast.show_message(f"Chỉnh sửa dòng {row_idx}", type="info")
    
    def _on_delete(self, row_idx: int):
        """Handle delete action"""
        self.toast.show_message(f"Xóa dòng {row_idx}", type="warning")


# ========================================
# MIGRATION GUIDE
# ========================================

"""
BEFORE (Old code with inline styles):

    header = QLabel("Tiêu đề")
    header.setStyleSheet("font-size: 20px; font-weight: 800; color: #334e88;")
    
    button = QPushButton("Click me")
    button.setStyleSheet("background-color: #334e88; color: white; padding: 10px;")
    
    table = QTableWidget()
    table.setStyleSheet("background-color: white; border: 1px solid #e0e0e0;")


AFTER (New code with theme):

    # 1. Apply theme once at app level
    theme = AppTheme()
    app.setStyleSheet(theme.get_stylesheet())
    
    # 2. Use object names for styling
    header = QLabel("Tiêu đề")
    header.setObjectName("title")  # Automatically styled!
    
    # 3. Use standard widgets
    button = QPushButton("Click me")  # Automatically styled!
    
    # 4. Use reusable widgets
    table = DataTable(headers=["Col1", "Col2"])  # Automatically styled!


BENEFITS:
- Consistent styling across entire app
- Easy to change theme (just edit theme.py)
- Less code duplication
- Better maintainability
- WCAG compliant colors
- Scalable layouts
"""


if __name__ == "__main__":
    import sys
    
    app = QApplication(sys.argv)
    
    # Apply theme globally
    theme = AppTheme()
    app.setStyleSheet(theme.get_stylesheet())
    
    window = ExampleWindow()
    window.setWindowTitle("Theme Example")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())
