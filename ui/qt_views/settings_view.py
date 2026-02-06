"""
Settings View - Cài đặt
Modern Premium Design
"""

import os
import shutil
from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QScrollArea, QSlider,
                             QVBoxLayout, QWidget)

from config import APP_NAME, APP_VERSION, BACKUP_DIR, DB_PATH
from ui.qt_theme import AppColors


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
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Content widget inside scroll
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(20)

        # UI Config section
        layout.addWidget(
            self._create_section("⚙️ Cấu hình giao diện", self._ui_config_content())
        )

        # Network section
        layout.addWidget(
            self._create_section("🌐 Kết nối điện thoại", self._network_content())
        )

        # Backup section
        layout.addWidget(
            self._create_section("💾 Sao lưu dữ liệu", self._backup_content())
        )

        # About section
        layout.addWidget(
            self._create_section("ℹ️ Thông tin ứng dụng", self._about_content())
        )

        layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

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
        row_height_slider.valueChanged.connect(
            lambda v: self._on_row_height_change(v, row_height_label)
        )
        row_height_layout.addWidget(row_height_slider)

        layout.addLayout(row_height_layout)

        # Widget Height
        widget_height_layout = QVBoxLayout()
        widget_height_label = QLabel(
            f"Chiều cao widget: {self.current_widget_height}px"
        )
        widget_height_label.setObjectName("subtitle")
        widget_height_layout.addWidget(widget_height_label)

        widget_height_slider = QSlider(Qt.Orientation.Horizontal)
        widget_height_slider.setMinimum(20)
        widget_height_slider.setMaximum(50)
        widget_height_slider.setValue(self.current_widget_height)
        widget_height_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        widget_height_slider.setTickInterval(5)
        widget_height_slider.valueChanged.connect(
            lambda v: self._on_widget_height_change(v, widget_height_label)
        )
        widget_height_layout.addWidget(widget_height_slider)

        layout.addLayout(widget_height_layout)

        # Reset button
        reset_btn = QPushButton("🔄 Đặt lại mặc định")
        reset_btn.setObjectName("secondary")
        reset_btn.setFixedWidth(180)
        reset_btn.clicked.connect(
            lambda: self._reset_defaults(
                row_height_slider,
                widget_height_slider,
                row_height_label,
                widget_height_label,
            )
        )
        layout.addWidget(reset_btn)

        # Info
        info = QLabel("💡 Điều chỉnh để fix vấn đề hiển thị box bị cắt")
        info.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-style: italic;"
        )
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
        desc = QLabel("Quét QR code để cấu hình tự động cho app Android:")
        desc.setObjectName("subtitle")
        layout.addWidget(desc)

        # QR Code Display
        qr_layout = QHBoxLayout()

        # QR Code Image
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(200, 200)
        self.qr_label.setStyleSheet(
            f"background: white; border: 2px solid {AppColors.BORDER}; border-radius: 8px;"
        )
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(self.qr_label)

        # Info column
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        # IP Display
        self.ip_label = QLabel("Đang lấy địa chỉ IP...")
        self.ip_label.setStyleSheet(f"""
            font-size: 16px; 
            font-weight: 700; 
            color: {AppColors.PRIMARY};
            background: {AppColors.BG};
            padding: 8px 12px;
            border-radius: 6px;
        """)
        info_layout.addWidget(self.ip_label)

        # Port info
        port = 5005  # default
        if self.container:
            config = self.container.get("config")
            if config:
                port = config.notification_port

        self.port_label = QLabel(f"Port: {port}")
        self.port_label.setStyleSheet(
            f"font-size: 14px; color: {AppColors.TEXT_SECONDARY};"
        )
        info_layout.addWidget(self.port_label)

        # Refresh button
        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self._refresh_ip)
        info_layout.addWidget(refresh_btn)

        info_layout.addStretch()
        qr_layout.addLayout(info_layout)

        layout.addLayout(qr_layout)

        # Manual URL guide
        guide = QLabel(f"💡 Hoặc nhập thủ công: http://[IP]:{port}")
        guide.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-style: italic; font-size: 11px;"
        )
        layout.addWidget(guide)

        self._refresh_ip()
        return content

    def _refresh_ip(self):
        import socket
        from io import BytesIO

        import qrcode
        from PyQt6.QtGui import QPixmap

        try:
            # Get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(ip)

            # Get port from config
            port = 5005
            if self.container:
                config = self.container.get("config")
                if config:
                    port = config.notification_port

            # Generate QR code with URL
            url = f"http://{ip}:{port}"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(url)
            qr.make(fit=True)

            # Create QR image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert PIL image to QPixmap
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)

            pixmap = QPixmap()
            pixmap.loadFromData(buffer.read())

            # Scale to fit label
            scaled_pixmap = pixmap.scaled(
                190,
                190,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.qr_label.setPixmap(scaled_pixmap)

        except Exception:
            self.ip_label.setText("127.0.0.1 (Chưa kết nối mạng)")
            self.qr_label.setText("❌\nKhông thể\ntạo QR")
            self.qr_label.setStyleSheet(
                f"background: {AppColors.BG}; border: 2px solid {AppColors.BORDER}; "
                f"border-radius: 8px; color: {AppColors.TEXT_SECONDARY}; font-size: 12px;"
            )

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
        layout.addLayout(
            self._info_row("Phiên bản", APP_VERSION, color=AppColors.PRIMARY)
        )
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
            QMessageBox.information(
                self, "Thành công", f"Đã sao lưu: {backup_file.name}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def _restore_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn file backup",
            str(BACKUP_DIR) if BACKUP_DIR.exists() else "",
            "Database (*.db)",
        )

        if not file_path:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Dữ liệu hiện tại sẽ bị thay thế. Tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                shutil.copy2(file_path, DB_PATH)
                QMessageBox.information(
                    self, "Thành công", "Đã khôi phục. Vui lòng khởi động lại."
                )
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))
