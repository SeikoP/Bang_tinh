"""
Settings View - Cài đặt
Clean Minimal Design
"""
import os
import shutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from ui.qt_theme import AppColors
from config import DB_PATH, BACKUP_DIR, APP_NAME, APP_VERSION


class SettingsView(QWidget):
    """View cài đặt"""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(16)
        
        # Header
        title = QLabel("Cài đặt")
        title.setObjectName("title")
        layout.addWidget(title)
        
        # Backup section
        layout.addWidget(self._create_section("Sao lưu dữ liệu", self._backup_content()))
        
        # About section
        layout.addWidget(self._create_section("Thông tin ứng dụng", self._about_content()))
        
        layout.addStretch()
    
    def _create_section(self, title: str, content: QWidget) -> QFrame:
        section = QFrame()
        section.setObjectName("card")
        section.setStyleSheet(f"""
            QFrame#card {{
                background-color: {AppColors.SURFACE};
                border: 1px solid {AppColors.BORDER};
                border-radius: 8px;
            }}
        """)
        
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(16, 14, 16, 14)
        section_layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; font-size: 14px;")
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
