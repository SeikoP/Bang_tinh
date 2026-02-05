"""
Settings View - Cài đặt
Modern Premium Design
"""
import os
import shutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox, QSlider, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from ui.qt_theme import AppColors
from config import DB_PATH, BACKUP_DIR, APP_NAME, APP_VERSION


class SettingsView(QWidget):
    """View cài đặt"""
    
    # Signals để thông báo thay đổi
    row_height_changed = pyqtSignal(int)
    widget_height_changed = pyqtSignal(int)
    
    def __init__(self, container=None):
        super().__init__()
        self.container = container
        self.current_row_height = 70
        self.current_widget_height = 28
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(20)
        
        # UI Config section
        layout.addWidget(self._create_section("⚙️ Cấu hình giao diện", self._ui_config_content()))
        
        # Network section
        layout.addWidget(self._create_section("🌐 Kết nối điện thoại", self._network_content()))
        
        # Backup section
        layout.addWidget(self._create_section("💾 Sao lưu dữ liệu", self._backup_content()))
        
        # About section
        layout.addWidget(self._create_section("ℹ️ Thông tin ứng dụng", self._about_content()))
        
        layout.addStretch()
    
    def _ui_config_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Row Height
        row_height_layout = QVBoxLayout()
        row_height_label = QLabel(f"Chiều cao hàng: {self.current_row_height}px")
        row_height_label.setObjectName("subtitle")
        row_height_layout.addWidget(row_height_label)
        
        row_height_slider = QSlider(Qt.Orientation.Horizontal)
        row_height_slider.setMinimum(40)
        row_height_slider.setMaximum(100)
        row_height_slider.setValue(self.current_row_height)
        row_height_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        row_height_slider.setTickInterval(10)
        row_height_slider.valueChanged.connect(lambda v: self._on_row_height_change(v, row_height_label))
        row_height_layout.addWidget(row_height_slider)
        
        layout.addLayout(row_height_layout)
        
        # Widget Height
        widget_height_layout = QVBoxLayout()
        widget_height_label = QLabel(f"Chiều cao widget: {self.current_widget_height}px")
        widget_height_label.setObjectName("subtitle")
        widget_height_layout.addWidget(widget_height_label)
        
        widget_height_slider = QSlider(Qt.Orientation.Horizontal)
        widget_height_slider.setMinimum(20)
        widget_height_slider.setMaximum(50)
        widget_height_slider.setValue(self.current_widget_height)
        widget_height_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        widget_height_slider.setTickInterval(5)
        widget_height_slider.valueChanged.connect(lambda v: self._on_widget_height_change(v, widget_height_label))
        widget_height_layout.addWidget(widget_height_slider)
        
        layout.addLayout(widget_height_layout)
        
        # Reset button
        reset_btn = QPushButton("🔄 Đặt lại mặc định")
        reset_btn.setObjectName("secondary")
        reset_btn.setFixedWidth(180)
        reset_btn.clicked.connect(lambda: self._reset_defaults(row_height_slider, widget_height_slider, row_height_label, widget_height_label))
        layout.addWidget(reset_btn)
        
        # Info
        info = QLabel("💡 Điều chỉnh để fix vấn đề hiển thị box bị cắt")
        info.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-style: italic;")
        layout.addWidget(info)
        
        return content
    
    def _on_row_height_change(self, value: int, label: QLabel):
        self.current_row_height = value
        label.setText(f"Chiều cao hàng: {value}px")
        self.row_height_changed.emit(value)
    
    def _on_widget_height_change(self, value: int, label: QLabel):
        self.current_widget_height = value
        label.setText(f"Chiều cao widget: {value}px")
        self.widget_height_changed.emit(value)
    
    def _reset_defaults(self, row_slider, widget_slider, row_label, widget_label):
        row_slider.setValue(70)
        widget_slider.setValue(28)
    
    def _network_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Title/Description
        desc = QLabel("Địa chỉ dùng để thiết lập trong MacroDroid:")
        desc.setObjectName("subtitle")
        layout.addWidget(desc)
        
        # IP Display
        self.ip_box = QHBoxLayout()
        self.ip_label = QLabel("Đang lấy địa chỉ IP...")
        self.ip_label.setStyleSheet(f"""
            font-size: 18px; 
            font-weight: 800; 
            color: {AppColors.PRIMARY};
            background: {AppColors.BG};
            padding: 10px;
            border-radius: 6px;
        """)
        self.ip_box.addWidget(self.ip_label)
        
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self._refresh_ip)
        self.ip_box.addWidget(refresh_btn)
        layout.addLayout(self.ip_box)
        
        # Guide
        # Get port from config if available
        port = 5005  # default
        if self.container:
            config = self.container.get('config')
            if config:
                port = config.notification_port
        
        guide = QLabel(f"Gợi ý URL: http://[Địa chỉ IP trên]:{port}?content={{not_text}}")
        guide.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-style: italic; font-size: 12px;")
        layout.addWidget(guide)
        
        self._refresh_ip()
        return content

    def _refresh_ip(self):
        import socket
        try:
            # Cách lấy IP nội bộ thực sự của máy
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(ip)
        except Exception:
            self.ip_label.setText("127.0.0.1 (Chưa kết nối mạng)")

    def _create_section(self, title: str, content: QWidget) -> QFrame:
        section = QFrame()
        section.setObjectName("card")
        
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(20, 18, 20, 18)
        section_layout.setSpacing(16)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-weight: 700;
            font-size: 16px;
            color: {AppColors.TEXT};
        """)
        section_layout.addWidget(title_label)
        
        section_layout.addWidget(content)
        
        return section
    
    def _backup_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Backup row
        backup_row = QHBoxLayout()
        backup_row.setSpacing(12)
        
        backup_label = QLabel("Tạo bản sao lưu database")
        backup_label.setObjectName("subtitle")
        backup_row.addWidget(backup_label)
        backup_row.addStretch()
        
        backup_btn = QPushButton("Sao lưu")
        backup_btn.setObjectName("success")
        backup_btn.clicked.connect(self._backup_database)
        backup_row.addWidget(backup_btn)
        
        layout.addLayout(backup_row)
        
        # Restore row
        restore_row = QHBoxLayout()
        restore_row.setSpacing(12)
        
        restore_label = QLabel("Khôi phục từ file backup")
        restore_label.setObjectName("subtitle")
        restore_row.addWidget(restore_label)
        restore_row.addStretch()
        
        restore_btn = QPushButton("Chọn file")
        restore_btn.setObjectName("secondary")
        restore_btn.clicked.connect(self._restore_database)
        restore_row.addWidget(restore_btn)
        
        layout.addLayout(restore_row)
        
        return content
    
    def _about_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addLayout(self._info_row("Tên ứng dụng", APP_NAME))
        layout.addLayout(self._info_row("Phiên bản", APP_VERSION, color=AppColors.PRIMARY))
        layout.addLayout(self._info_row("Database", str(DB_PATH.name)))
        layout.addLayout(self._info_row("Framework", "PyQt6", color=AppColors.SUCCESS))
        
        return content
    
    def _info_row(self, label: str, value: str, color: str = None) -> QHBoxLayout:
        row = QHBoxLayout()
        
        lbl = QLabel(label + ":")
        lbl.setObjectName("subtitle")
        row.addWidget(lbl)
        
        row.addStretch()
        
        val = QLabel(value)
        if color:
            val.setStyleSheet(f"color: {color}; font-weight: 500;")
        row.addWidget(val)
        
        return row
    
    def _backup_database(self):
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f"backup_{timestamp}.db"
            shutil.copy2(DB_PATH, backup_file)
            QMessageBox.information(self, "Thành công", f"Đã sao lưu: {backup_file.name}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))
    
    def _restore_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file backup",
            str(BACKUP_DIR) if BACKUP_DIR.exists() else "",
            "Database (*.db)"
        )
        
        if not file_path:
            return
        
        reply = QMessageBox.question(
            self, "Xác nhận",
            "Dữ liệu hiện tại sẽ bị thay thế. Tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.copy2(file_path, DB_PATH)
                QMessageBox.information(self, "Thành công", "Đã khôi phục. Vui lòng khởi động lại.")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))
