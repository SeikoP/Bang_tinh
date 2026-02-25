"""
Settings View - Cài đặt
Modern Premium Design
"""

import json
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                             QHBoxLayout, QLabel, QMessageBox, QPushButton,
                             QScrollArea, QSlider, QVBoxLayout, QWidget)


class NoWheelComboBox(QComboBox):
    """Custom ComboBox that ignores wheel events to prevent accidental changes while scrolling"""

    def wheelEvent(self, event):
        event.ignore()


from ...core.constants import APP_NAME, APP_VERSION
from ...core.config import BACKUPS as BACKUP_DIR
from ..theme import AppColors


class SettingsView(QWidget):
    """View cài đặt"""

    # Signals để thông báo thay đổi
    row_height_changed = pyqtSignal(int)
    widget_height_changed = pyqtSignal(int)

    class IPWorker(QThread):
        finished = pyqtSignal(str, int, str, object, list)  # IP, Port, SecretKey, QPixmap, AllIPs
        error = pyqtSignal()

        def __init__(self, container=None):
            super().__init__()
            self.container = container

        def run(self):
            from io import BytesIO

            import qrcode
            from PyQt6.QtGui import QPixmap

            try:
                # Get all local IPs
                from ...network.discovery_server import get_all_local_ips
                ips = get_all_local_ips()
                ip = ips[0] if ips else "127.0.0.1"

                # Get port and secret key from config
                port = 5005
                secret_key = ""
                if self.container:
                    config = self.container.get("config")
                    if config:
                        port = config.notification_port
                        secret_key = config.secret_key

                # Generate QR code with JSON data
                # h=primary host, p=port, k=key, ips=all fallback IPs
                qr_data = json.dumps({"h": ip, "p": port, "k": secret_key, "ips": ips})

                qr = qrcode.QRCode(version=1, box_size=10, border=2)
                qr.add_data(qr_data)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")

                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.read())

                self.finished.emit(ip, port, secret_key, pixmap, ips)
            except Exception as e:
                if self.container:
                    logger = self.container.get("logger")
                    if logger:
                        logger.error(f"Failed to generate QR or get IP: {e}", exc_info=True)
                self.error.emit()

    def __init__(self, container=None):
        super().__init__()
        self.container = container
        self.current_row_height = 70
        self.current_widget_height = 28
        self.current_machine_count = 46

        # Explicitly set background style
        self.setStyleSheet(f"background-color: {AppColors.BG};")
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
            self._create_section("Cấu hình giao diện", self._ui_config_content())
        )

        # TTS section
        layout.addWidget(
            self._create_section("Thông báo âm thanh", self._tts_content())
        )

        # Network section
        layout.addWidget(
            self._create_section("Kết nối điện thoại", self._network_content())
        )

        # Backup section
        layout.addWidget(
            self._create_section("Sao lưu dữ liệu", self._backup_content())
        )

        # About section
        layout.addWidget(
            self._create_section("Thông tin ứng dụng", self._about_content())
        )

        layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Defer construction of some heavy sections to eliminate initial delay
        self._deferred_timer = QTimer(self)
        self._deferred_timer.setSingleShot(True)
        self._deferred_timer.timeout.connect(self._late_init_ui)
        self._deferred_timer.start(50)

    def _late_init_ui(self):
        """Construct parts of UI after current thread is free"""
        # Additional heavy UI elements can be added here if needed
        pass

    def _ui_config_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Machine count configuration
        machine_layout = QVBoxLayout()
        machine_label = QLabel("Số lượng máy: 46")
        machine_label.setObjectName("subtitle")
        machine_layout.addWidget(machine_label)

        machine_slider = QSlider(Qt.Orientation.Horizontal)
        machine_slider.setMinimum(1)
        machine_slider.setMaximum(100)
        machine_slider.setValue(46)
        machine_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        machine_slider.setTickInterval(10)
        machine_slider.valueChanged.connect(
            lambda v: self._on_machine_count_change(v, machine_label)
        )
        machine_layout.addWidget(machine_slider)

        layout.addLayout(machine_layout)

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
        reset_btn = QPushButton("Đặt lại mặc định")
        reset_btn.setObjectName("secondary")
        reset_btn.setFixedWidth(180)
        reset_btn.clicked.connect(
            lambda: self._reset_defaults(
                machine_slider,
                row_height_slider,
                widget_height_slider,
                machine_label,
                row_height_label,
                widget_height_label,
            )
        )
        layout.addWidget(reset_btn)

        # Info
        info = QLabel("Điều chỉnh để fix vấn đề hiển thị box bị cắt")
        info.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-style: italic;"
        )
        layout.addWidget(info)

        return content

    def _on_machine_count_change(self, value: int, label: QLabel):
        self.current_machine_count = value
        label.setText(f"Số lượng máy: {value}")

    def _on_row_height_change(self, value: int, label: QLabel):
        self.current_row_height = value
        label.setText(f"Chiều cao hàng: {value}px")
        self.row_height_changed.emit(value)

    def _on_widget_height_change(self, value: int, label: QLabel):
        self.current_widget_height = value
        label.setText(f"Chiều cao widget: {value}px")
        self.widget_height_changed.emit(value)

    def _reset_defaults(
        self,
        machine_slider,
        row_slider,
        widget_slider,
        machine_label,
        row_label,
        widget_label,
    ):
        machine_slider.setValue(46)
        row_slider.setValue(70)
        widget_slider.setValue(28)

    def _tts_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Enable/Disable TTS
        enable_layout = QHBoxLayout()
        enable_label = QLabel("Bật thông báo âm thanh")
        enable_label.setObjectName("subtitle")
        enable_layout.addWidget(enable_label)
        enable_layout.addStretch()

        self.tts_enabled_checkbox = QCheckBox()
        self.tts_enabled_checkbox.setChecked(True)
        self.tts_enabled_checkbox.stateChanged.connect(self._on_tts_enabled_changed)
        enable_layout.addWidget(self.tts_enabled_checkbox)

        layout.addLayout(enable_layout)

        # Voice selection
        voice_layout = QVBoxLayout()
        voice_label = QLabel("Giọng đọc")
        voice_label.setObjectName("subtitle")
        voice_layout.addWidget(voice_label)

        self.voice_combo = NoWheelComboBox()
        self.voice_combo.addItem("Hoài Mỹ (Nữ, Miền Nam)", "edge_female")
        self.voice_combo.addItem("Thương (Nữ, Miền Bắc)", "edge_north_female")
        self.voice_combo.addItem("Nam Minh (Nam, Miền Bắc)", "edge_male")
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        voice_layout.addWidget(self.voice_combo)

        layout.addLayout(voice_layout)

        # Volume control
        volume_layout = QVBoxLayout()
        self.volume_label = QLabel("Âm lượng: 100%")
        self.volume_label.setObjectName("subtitle")
        volume_layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self.volume_slider)

        layout.addLayout(volume_layout)

        # Test button
        test_btn = QPushButton("🔊 Thử giọng đọc")
        test_btn.setObjectName("primary")
        test_btn.setFixedWidth(180)
        test_btn.clicked.connect(self._test_tts)
        layout.addWidget(test_btn)

        # Info
        info = QLabel("Thông báo sẽ đọc số tiền và tên người gửi khi có giao dịch")
        info.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-style: italic;"
        )
        layout.addWidget(info)

        return content

    def _on_tts_enabled_changed(self, state):
        """Handle TTS enable/disable"""
        enabled = state == Qt.CheckState.Checked.value
        self.voice_combo.setEnabled(enabled)
        self.volume_slider.setEnabled(enabled)
        if self.container:
            tts_service = self.container.get("tts_service")
            if tts_service:
                tts_service.set_enabled(enabled)

    def _on_voice_changed(self, index):
        """Handle voice selection change"""
        voice = self.voice_combo.itemData(index)
        if self.container:
            tts_service = self.container.get("tts_service")
            if tts_service:
                tts_service.set_voice(voice)

    def _on_volume_changed(self, value):
        """Handle volume change"""
        self.volume_label.setText(f"Âm lượng: {value}%")
        if self.container:
            tts_service = self.container.get("tts_service")
            if tts_service:
                tts_service.set_volume(value)

    def _test_tts(self):
        """Test TTS with sample message"""
        if self.container:
            tts_service = self.container.get("tts_service")
            if tts_service:
                voice_name = self.voice_combo.currentText().split(" (")[0]
                sample_text = f"Xin chào, tôi là {voice_name}. Tôi sẽ giúp bạn thông báo khi có tiền về. Chúc bạn một ngày làm việc hiệu quả!"
                tts_service.speak(sample_text)
            else:
                QMessageBox.warning(self, "Lỗi", "TTS service không khả dụng")
        else:
            QMessageBox.warning(self, "Lỗi", "Container không khả dụng")

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
        self.port_label = QLabel("Port: 5005")
        self.port_label.setStyleSheet(
            f"font-size: 14px; color: {AppColors.TEXT_SECONDARY};"
        )
        info_layout.addWidget(self.port_label)

        # Key info
        self.key_label = QLabel("Key: ...")
        self.key_label.setStyleSheet(
            f"font-size: 13px; color: {AppColors.TEXT_SECONDARY}; font-family: monospace;"
        )
        info_layout.addWidget(self.key_label)

        # Refresh button
        refresh_btn = QPushButton("Làm mới")
        refresh_btn.setFixedWidth(120)
        refresh_btn.clicked.connect(self._refresh_ip)
        info_layout.addWidget(refresh_btn)

        info_layout.addStretch()
        qr_layout.addLayout(info_layout)

        layout.addLayout(qr_layout)

        # Manual URL guide
        guide = QLabel("Hoặc nhập thủ công URL và Key hiển thị ở trên")
        guide.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-style: italic; font-size: 11px;"
        )
        layout.addWidget(guide)

        # Initial refresh
        QTimer.singleShot(500, self._refresh_ip)
        return content

    def _refresh_ip(self):
        """Async refresh IP & QR"""
        self.ip_label.setText("Đang lấy IP...")
        self._worker = self.IPWorker(self.container)
        self._worker.finished.connect(self._on_ip_ready)
        self._worker.error.connect(lambda: self.ip_label.setText("127.0.0.1 (Offline)"))
        self._worker.start()

    def _on_ip_ready(self, ip, port, secret_key, pixmap, ips):
        # Show all IPs if multiple adapters
        if len(ips) > 1:
            self.ip_label.setText(ip)
            self.ip_label.setToolTip("Tất cả IPs: " + ", ".join(ips))
        else:
            self.ip_label.setText(ip)
        self.port_label.setText(f"Port: {port}  •  UDP Discovery: {port + 1}")
        # Show partial key for verification
        short_key = secret_key[:8] + "..." if secret_key else "None"
        self.key_label.setText(f"Key: {short_key}")

        scaled = pixmap.scaled(
            190,
            190,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.qr_label.setPixmap(scaled)

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

        # Auto-backup status
        status_label = QLabel("Tự động sao lưu: Đang bật")
        status_label.setStyleSheet(f"color: {AppColors.SUCCESS}; font-weight: 600;")
        layout.addWidget(status_label)

        info = QLabel(
            "• Sao lưu khi khởi động\n• Sao lưu khi tắt app\n• Sao lưu hàng ngày"
        )
        info.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(info)

        # Buttons
        btns = QHBoxLayout()
        backup_btn = QPushButton("Sao lưu ngay")
        backup_btn.setObjectName("success")
        backup_btn.clicked.connect(self._backup_database)
        btns.addWidget(backup_btn)

        restore_btn = QPushButton("📂 Khôi phục")
        restore_btn.setObjectName("secondary")
        restore_btn.clicked.connect(self._restore_database)
        btns.addWidget(restore_btn)

        layout.addLayout(btns)
        return content

    def _about_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addLayout(self._info_row("Tên ứng dụng", APP_NAME))
        layout.addLayout(
            self._info_row("Phiên bản", APP_VERSION, color=AppColors.PRIMARY)
        )
        return content

    def _info_row(self, label: str, value: str, color: str | None = None) -> QHBoxLayout:
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
            if self.container:
                bs = self.container.get("backup_service")
                if bs:
                    f = bs.create_backup(prefix="manual")
                    QMessageBox.information(self, "Thành công", f"Đã sao lưu: {f.name}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", str(e))

    def _restore_database(self):
        f_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file backup", str(BACKUP_DIR), "Database (*.db)"
        )
        if not f_path:
            return
        if (
            QMessageBox.question(
                self,
                "Xác nhận",
                "Ghi đè dữ liệu hiện tại?",
                QMessageBox.StandardButton.Yes,
            )
            == QMessageBox.StandardButton.Yes
        ):
            try:
                if self.container:
                    bs = self.container.get("backup_service")
                    if bs:
                        bs.restore_backup(Path(f_path))
                        QMessageBox.information(
                            self, "Thành công", "Đã khôi phục. Hãy khởi động lại."
                        )
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", str(e))
