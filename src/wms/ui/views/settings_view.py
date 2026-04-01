"""
Settings View - Cài đặt
Modern Premium Design
"""

import json
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QFileDialog, QFrame,
                             QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                             QPushButton, QScrollArea, QSlider, QVBoxLayout,
                             QWidget)


class NoWheelComboBox(QComboBox):
    """Custom ComboBox that ignores wheel events to prevent accidental changes while scrolling"""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelSlider(QSlider):
    """Custom Slider that ignores wheel events to prevent accidental changes while scrolling"""

    def wheelEvent(self, event):
        event.ignore()


class NoWheelCheckBox(QCheckBox):
    """Custom CheckBox that ignores wheel events to prevent accidental toggling while scrolling"""

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

        def __init__(self, container=None, tunnel_url: str = ""):
            super().__init__()
            self.container = container
            self.tunnel_url = tunnel_url.strip()

        def run(self):
            from io import BytesIO

            import qrcode
            from PyQt6.QtGui import QPixmap

            try:
                # Get all local IPs
                from ...network.network_monitor import get_best_ip, get_all_ips_flat
                best_ip, best_type = get_best_ip()
                ips = get_all_ips_flat()
                ip = best_ip if best_ip != "127.0.0.1" else (ips[0] if ips else "127.0.0.1")

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
                # If tunnel URL is set, include it as "t" field for remote access
                qr_payload = {"h": ip, "p": port, "k": secret_key, "ips": ips}
                if self.tunnel_url:
                    qr_payload["t"] = self.tunnel_url
                qr_data = json.dumps(qr_payload)

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

        # Bank account section
        layout.addWidget(
            self._create_section("Tài khoản ngân hàng (VietQR)", self._bank_content())
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

        machine_slider = NoWheelSlider(Qt.Orientation.Horizontal)
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

        row_height_slider = NoWheelSlider(Qt.Orientation.Horizontal)
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

        widget_height_slider = NoWheelSlider(Qt.Orientation.Horizontal)
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

        self.tts_enabled_checkbox = NoWheelCheckBox()
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

        self.volume_slider = NoWheelSlider(Qt.Orientation.Horizontal)
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

        # ── Auto-Tunnel section ──
        tunnel_header = QLabel("🌐 Kết nối từ xa (khác WiFi)")
        tunnel_header.setStyleSheet(f"""
            font-weight: 700; font-size: 13px; color: {AppColors.TEXT};
            margin-top: 12px;
        """)
        layout.addWidget(tunnel_header)

        tunnel_desc = QLabel(
            "Tự động tạo tunnel để điện thoại kết nối từ xa (không cần cùng WiFi).\n"
            "Cloudflare nhanh hơn và không cần đăng ký. Ngrok cần authtoken miễn phí."
        )
        tunnel_desc.setWordWrap(True)
        tunnel_desc.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; line-height: 1.4;"
        )
        layout.addWidget(tunnel_desc)

        # ── Provider selector row ──
        provider_row = QHBoxLayout()
        provider_label = QLabel("Dịch vụ:")
        provider_label.setFixedWidth(60)
        provider_label.setStyleSheet(f"color: {AppColors.TEXT}; font-size: 12px;")
        provider_row.addWidget(provider_label)

        self.tunnel_provider_combo = NoWheelComboBox()
        self.tunnel_provider_combo.addItem("☁️  Cloudflare Tunnel (khuyên dùng)", "cloudflare")
        self.tunnel_provider_combo.addItem("🔗  ngrok", "ngrok")
        self.tunnel_provider_combo.setFixedWidth(300)
        self.tunnel_provider_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 10px;
                border: 1px solid {AppColors.BORDER};
                border-radius: 6px;
                font-size: 12px;
                background: white;
            }}
        """)
        self.tunnel_provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        provider_row.addWidget(self.tunnel_provider_combo)
        provider_row.addStretch()
        layout.addLayout(provider_row)

        # ── Authtoken row (hidden by default — only for ngrok) ──
        self.ngrok_token_widget = QWidget()
        token_row = QHBoxLayout(self.ngrok_token_widget)
        token_row.setContentsMargins(0, 0, 0, 0)
        token_label = QLabel("Authtoken:")
        token_label.setFixedWidth(75)
        token_label.setStyleSheet(f"color: {AppColors.TEXT}; font-size: 12px;")
        token_row.addWidget(token_label)

        self.ngrok_token_input = QLineEdit()
        self.ngrok_token_input.setPlaceholderText("Dán authtoken ngrok vào đây (chỉ cần lần đầu)")
        self.ngrok_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ngrok_token_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 6px 10px;
                border: 1px solid {AppColors.BORDER};
                border-radius: 6px;
                font-size: 12px;
                background: white;
            }}
            QLineEdit:focus {{
                border-color: {AppColors.PRIMARY};
            }}
        """)
        self._load_ngrok_token()
        token_row.addWidget(self.ngrok_token_input)
        self.ngrok_token_widget.setVisible(False)  # hidden — cloudflare is default
        layout.addWidget(self.ngrok_token_widget)

        # ── Start/Stop button row ──
        tunnel_btn_row = QHBoxLayout()

        self.tunnel_toggle_btn = QPushButton("Bật Cloudflare Tunnel")
        self.tunnel_toggle_btn.setFixedWidth(220)
        self.tunnel_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY}; color: white;
                padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        self.tunnel_toggle_btn.clicked.connect(self._toggle_tunnel)
        tunnel_btn_row.addWidget(self.tunnel_toggle_btn)

        self.tunnel_url_label = QLabel("")
        self.tunnel_url_label.setStyleSheet(f"""
            color: {AppColors.TEXT}; font-size: 12px;
            padding: 6px 10px;
            border: 1px solid {AppColors.BORDER};
            border-radius: 6px;
            background: #f8fafc;
        """)
        self.tunnel_url_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        tunnel_btn_row.addWidget(self.tunnel_url_label, 1)
        layout.addLayout(tunnel_btn_row)

        self.tunnel_status = QLabel("")
        self.tunnel_status.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.tunnel_status)

        # ── Manual tunnel URL (fallback) ──
        manual_header = QLabel("Hoặc nhập URL tunnel thủ công:")
        manual_header.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; margin-top: 6px;"
        )
        layout.addWidget(manual_header)

        tunnel_row = QHBoxLayout()
        self.tunnel_input = QLineEdit()
        self.tunnel_input.setPlaceholderText("VD: https://abc123.ngrok-free.app hoặc https://xxx.trycloudflare.com")
        self.tunnel_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                border: 1px solid {AppColors.BORDER};
                border-radius: 6px;
                font-size: 13px;
                background: white;
            }}
            QLineEdit:focus {{
                border-color: {AppColors.PRIMARY};
            }}
        """)
        tunnel_row.addWidget(self.tunnel_input)

        tunnel_apply_btn = QPushButton("Tạo QR")
        tunnel_apply_btn.setFixedWidth(80)
        tunnel_apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY}; color: white;
                padding: 8px; border-radius: 6px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        tunnel_apply_btn.clicked.connect(self._refresh_ip)
        tunnel_row.addWidget(tunnel_apply_btn)
        layout.addLayout(tunnel_row)

        # ── Init tunnel service reference ──
        self._tunnel_service = None

        # Initial refresh
        QTimer.singleShot(500, self._refresh_ip)
        return content

    # ── Tunnel helpers ──────────────────────────────────────
    def _on_provider_changed(self, index: int):
        """Show/hide authtoken field based on selected provider."""
        provider = self.tunnel_provider_combo.currentData()
        is_ngrok = provider == "ngrok"
        self.ngrok_token_widget.setVisible(is_ngrok)
        label = "Bật ngrok" if is_ngrok else "Bật Cloudflare Tunnel"
        if not (self._tunnel_service and self._tunnel_service.is_running):
            self.tunnel_toggle_btn.setText(label)
            self.tunnel_toggle_btn.setFixedWidth(220)

    def _load_ngrok_token(self):
        """Load saved ngrok authtoken from config."""
        try:
            from ...core.config import Config
            config = Config.from_env()
            token = getattr(config, "ngrok_authtoken", "") or ""
            if not token:
                import os
                token = os.environ.get("NGROK_AUTHTOKEN", "")
            if token:
                self.ngrok_token_input.setText(token)
        except Exception:
            pass

    def _save_ngrok_token(self, token: str):
        """Persist ngrok authtoken to .env."""
        try:
            from pathlib import Path
            env_file = Path(".env")
            lines = []
            found = False
            if env_file.exists():
                lines = env_file.read_text(encoding="utf-8").splitlines()
                for i, line in enumerate(lines):
                    if line.startswith("NGROK_AUTHTOKEN="):
                        lines[i] = f"NGROK_AUTHTOKEN={token}"
                        found = True
                        break
            if not found:
                lines.append(f"NGROK_AUTHTOKEN={token}")
            env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception:
            pass

    def _toggle_tunnel(self):
        """Start or stop the selected tunnel provider."""
        from ...services.tunnel_service import TunnelService

        if self._tunnel_service and self._tunnel_service.is_running:
            self.tunnel_toggle_btn.setText("Đang dừng...")
            self.tunnel_toggle_btn.setEnabled(False)
            self._tunnel_service.stop()
            self._tunnel_service = None
            provider = self.tunnel_provider_combo.currentData()
            label = "Bật ngrok" if provider == "ngrok" else "Bật Cloudflare Tunnel"
            self.tunnel_toggle_btn.setText(label)
            self.tunnel_toggle_btn.setEnabled(True)
            self.tunnel_toggle_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {AppColors.PRIMARY}; color: white;
                    padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px;
                }}
                QPushButton:hover {{ background: #059669; }}
            """)
            self.tunnel_url_label.setText("")
            self.tunnel_status.setText("Tunnel đã tắt")
            self.tunnel_status.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
            self.tunnel_input.clear()
            self._write_tunnel_state("", status="down", provider=provider)
            self._refresh_ip()
            return

        provider = self.tunnel_provider_combo.currentData()
        token = self.ngrok_token_input.text().strip() if provider == "ngrok" else ""
        if token:
            self._save_ngrok_token(token)

        port = 5005
        if self.container:
            config = self.container.get("config")
            if config:
                port = config.notification_port

        self._tunnel_service = TunnelService(parent=self)
        self._tunnel_service.tunnel_started.connect(self._on_tunnel_started)
        self._tunnel_service.tunnel_error.connect(self._on_tunnel_error)
        self._tunnel_service.tunnel_stopped.connect(self._on_tunnel_stopped)
        self._tunnel_service.progress.connect(self._on_tunnel_progress)

        self.tunnel_toggle_btn.setText("Đang kết nối...")
        self.tunnel_toggle_btn.setEnabled(False)
        self.tunnel_status.setText("Đang khởi động...")
        self.tunnel_status.setStyleSheet(f"color: {AppColors.WARNING}; font-size: 11px;")

        self._tunnel_service.start(port, provider=provider, authtoken=token)

    def _on_tunnel_progress(self, msg: str):
        self.tunnel_status.setText(f"⏳ {msg}")
        self.tunnel_status.setStyleSheet(f"color: {AppColors.WARNING}; font-size: 11px;")

    def _on_tunnel_started(self, url: str):
        self.tunnel_toggle_btn.setText("Tắt tunnel")
        self.tunnel_toggle_btn.setEnabled(True)
        self.tunnel_toggle_btn.setFixedWidth(220)
        self.tunnel_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: #ef4444; color: white;
                padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px;
            }}
            QPushButton:hover {{ background: #dc2626; }}
        """)
        self.tunnel_url_label.setText(url)
        provider_name = self._tunnel_service.provider if self._tunnel_service else "tunnel"
        self.tunnel_status.setText(f"{provider_name} đang chạy — URL đã thêm vào QR code")
        self.tunnel_status.setStyleSheet(f"color: {AppColors.SUCCESS}; font-size: 11px;")
        self.tunnel_input.setText(url)
        self._write_tunnel_state(url, status="up", provider=provider_name)
        self._refresh_ip()

    def _on_tunnel_error(self, msg: str):
        provider = self.tunnel_provider_combo.currentData()
        label = "Bật ngrok" if provider == "ngrok" else "Bật Cloudflare Tunnel"
        self.tunnel_toggle_btn.setText(label)
        self.tunnel_toggle_btn.setEnabled(True)
        self.tunnel_toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY}; color: white;
                padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px;
            }}
            QPushButton:hover {{ background: #059669; }}
        """)
        self.tunnel_url_label.setText("")
        self.tunnel_status.setText(f"Lỗi: {msg}")
        self.tunnel_status.setStyleSheet(f"color: #ef4444; font-size: 11px;")
        provider = self.tunnel_provider_combo.currentData()
        self._write_tunnel_state("", status="error", provider=provider)

    def _on_tunnel_stopped(self):
        provider = self.tunnel_provider_combo.currentData()
        label = "Bật ngrok" if provider == "ngrok" else "Bật Cloudflare Tunnel"
        self.tunnel_toggle_btn.setText(label)
        self.tunnel_toggle_btn.setEnabled(True)
        provider = self.tunnel_provider_combo.currentData()
        self._write_tunnel_state("", status="down", provider=provider)

    def _refresh_ip(self):
        """Async refresh IP & QR"""
        self.ip_label.setText("Đang lấy IP...")
        tunnel_url = self.tunnel_input.text().strip() if hasattr(self, 'tunnel_input') else ""
        self._worker = self.IPWorker(self.container, tunnel_url=tunnel_url)
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

        # Show tunnel status
        if hasattr(self, 'tunnel_status') and hasattr(self, 'tunnel_input'):
            tunnel_url = self.tunnel_input.text().strip()
            if tunnel_url:
                self.tunnel_status.setText(f"✅ QR bao gồm tunnel URL: {tunnel_url}")
                self.tunnel_status.setStyleSheet(f"color: {AppColors.SUCCESS}; font-size: 11px;")
            else:
                self.tunnel_status.setText("")

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

    # ── Bank Account Section ──────────────────────────────────────────────
    _BANK_CFG_PATH = Path(__file__).parents[3] / "config" / "bank_settings.json"
    _BANK_PROFILES_PATH = Path(__file__).parents[3] / "config" / "bank_profiles.json"
    _TUNNEL_STATE_PATH = Path(__file__).parents[3] / "config" / "tunnel_state.json"

    def _write_tunnel_state(self, url: str, status: str = "up", provider: str = ""):
        """Persist current tunnel URL so notification_service can expose it via /api/config."""
        try:
            import time
            self._TUNNEL_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._TUNNEL_STATE_PATH.write_text(
                json.dumps(
                    {
                        "tunnel_url": url,
                        "status": status,
                        "provider": provider,
                        "updated_at": int(time.time()),
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _bank_content(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(10)

        desc = QLabel(
            "Thông tin dùng để tạo mã QR VietQR. Lưu template để chuyển đổi nhanh giữa các tài khoản."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(desc)

        # Saved profiles selector
        profile_row = QHBoxLayout()
        profile_label = QLabel("TK đã lưu:")
        profile_label.setFixedWidth(80)
        profile_label.setStyleSheet(f"color: {AppColors.TEXT}; font-size: 12px; font-weight: 600;")
        profile_row.addWidget(profile_label)

        self._bank_profile_combo = NoWheelComboBox()
        self._bank_profile_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 10px; border: 1px solid {AppColors.BORDER};
                border-radius: 6px; font-size: 12px; background: white;
            }}
        """)
        self._bank_profile_combo.currentIndexChanged.connect(self._on_bank_profile_selected)
        profile_row.addWidget(self._bank_profile_combo, 1)

        del_profile_btn = QPushButton("Xoa")
        del_profile_btn.setFixedSize(50, 32)
        del_profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.ERROR}; color: white; border: none;
                border-radius: 5px; font-size: 11px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #B91C1C; }}
        """)
        del_profile_btn.clicked.connect(self._delete_bank_profile)
        profile_row.addWidget(del_profile_btn)

        layout.addLayout(profile_row)

        # Load current active values
        saved = {}
        if self._BANK_CFG_PATH.exists():
            try:
                saved = json.loads(self._BANK_CFG_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass

        # BIN helper row
        bin_helper_row = QHBoxLayout()
        bin_helper_label = QLabel("Tra BIN:")
        bin_helper_label.setFixedWidth(80)
        bin_helper_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
        bin_helper_row.addWidget(bin_helper_label)

        self._bin_quick_combo = NoWheelComboBox()
        self._bin_quick_combo.addItem("-- Chọn ngân hàng --", "")
        for name, bin_code in [
            ("VietinBank", "970415"), ("Vietcombank", "970436"), ("MB Bank", "970422"),
            ("Techcombank", "970407"), ("ACB", "970416"), ("BIDV", "970418"),
            ("Agribank", "970405"), ("TPBank", "970423"), ("Sacombank", "970403"),
            ("VPBank", "970432"), ("SHB", "970443"), ("VIB", "970441"),
        ]:
            self._bin_quick_combo.addItem(f"{name} ({bin_code})", bin_code)
        self._bin_quick_combo.currentIndexChanged.connect(
            lambda: self._bank_bin.setText(self._bin_quick_combo.currentData() or "")
        )
        self._bin_quick_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 8px; border: 1px solid {AppColors.BORDER};
                border-radius: 5px; font-size: 11px; background: #f8fafc;
            }}
        """)
        bin_helper_row.addWidget(self._bin_quick_combo, 1)
        layout.addLayout(bin_helper_row)

        # Form fields
        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        def _field(label, key, placeholder=""):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFixedWidth(140)
            lbl.setStyleSheet(f"color: {AppColors.TEXT}; font-size: 12px;")
            inp = QLineEdit(saved.get(key, ""))
            inp.setPlaceholderText(placeholder)
            inp.setStyleSheet(
                f"padding: 6px 10px; border: 1px solid {AppColors.BORDER}; "
                f"border-radius: 6px; font-size: 12px;"
            )
            row.addWidget(lbl)
            row.addWidget(inp, 1)
            return row, inp

        bin_row, self._bank_bin = _field("BIN ngân hàng:", "bin", "970415")
        acc_row, self._bank_account = _field("Số tài khoản:", "account", "1234567890")
        holder_row, self._bank_holder = _field("Tên chủ TK:", "holder", "NGUYEN VAN A")

        form_layout.addLayout(bin_row)
        form_layout.addLayout(acc_row)
        form_layout.addLayout(holder_row)
        layout.addLayout(form_layout)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        save_btn = QPushButton("Luu lam TK hien tai")
        save_btn.setFixedHeight(36)
        save_btn.setObjectName("primary")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_bank_settings)
        btn_row.addWidget(save_btn)

        save_tpl_btn = QPushButton("Luu thanh template")
        save_tpl_btn.setFixedHeight(36)
        save_tpl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_tpl_btn.setStyleSheet(f"""
            QPushButton {{
                background: #3b82f6; color: white; border: none;
                border-radius: 6px; font-weight: 600; font-size: 12px;
            }}
            QPushButton:hover {{ background: #2563eb; }}
        """)
        save_tpl_btn.clicked.connect(self._save_bank_profile)
        btn_row.addWidget(save_tpl_btn)

        layout.addLayout(btn_row)

        # Load profiles into combo
        self._refresh_bank_profiles()

        return content

    def _load_bank_profiles(self) -> list:
        """Load saved bank profiles from disk"""
        if self._BANK_PROFILES_PATH.exists():
            try:
                return json.loads(self._BANK_PROFILES_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save_bank_profiles_to_disk(self, profiles: list):
        self._BANK_PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._BANK_PROFILES_PATH.write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _refresh_bank_profiles(self):
        """Reload profile combo from disk"""
        self._bank_profile_combo.blockSignals(True)
        self._bank_profile_combo.clear()
        self._bank_profile_combo.addItem("-- Chon template --", None)
        profiles = self._load_bank_profiles()
        for p in profiles:
            label = f"{p.get('holder', '?')} - {p.get('account', '?')} ({p.get('bin', '?')})"
            self._bank_profile_combo.addItem(label, p)
        self._bank_profile_combo.blockSignals(False)

    def _on_bank_profile_selected(self, index):
        """Fill form from selected profile AND auto-save as active bank account"""
        profile = self._bank_profile_combo.currentData()
        if not profile or not isinstance(profile, dict):
            return
        self._bank_bin.setText(profile.get("bin", ""))
        self._bank_account.setText(profile.get("account", ""))
        self._bank_holder.setText(profile.get("holder", ""))
        # Auto-save as active bank settings so QR dialog picks it up immediately
        self._auto_save_bank(profile)

    def _save_bank_profile(self):
        """Save current form as a reusable template"""
        data = {
            "bin": self._bank_bin.text().strip(),
            "account": self._bank_account.text().strip(),
            "holder": self._bank_holder.text().strip().upper(),
        }
        if not data["bin"] or not data["account"]:
            QMessageBox.warning(self, "Thiếu thông tin", "Cần nhập BIN và số tài khoản để lưu template.")
            return

        profiles = self._load_bank_profiles()
        # Check duplicate by account number
        for i, p in enumerate(profiles):
            if p.get("account") == data["account"] and p.get("bin") == data["bin"]:
                profiles[i] = data  # Update existing
                break
        else:
            profiles.append(data)

        self._save_bank_profiles_to_disk(profiles)
        self._refresh_bank_profiles()
        QMessageBox.information(self, "OK", f"Đã lưu template: {data['holder']} - {data['account']}")

    def _delete_bank_profile(self):
        """Delete the currently selected profile"""
        profile = self._bank_profile_combo.currentData()
        if not profile or not isinstance(profile, dict):
            return
        profiles = self._load_bank_profiles()
        profiles = [p for p in profiles
                    if not (p.get("account") == profile.get("account")
                            and p.get("bin") == profile.get("bin"))]
        self._save_bank_profiles_to_disk(profiles)
        self._refresh_bank_profiles()

    def _save_bank_settings(self):
        data = {
            "bin": self._bank_bin.text().strip(),
            "account": self._bank_account.text().strip(),
            "holder": self._bank_holder.text().strip().upper(),
        }
        if not data["bin"] or not data["account"]:
            QMessageBox.warning(self, "Thiếu thông tin", "Vui lòng nhập BIN và số tài khoản.")
            return
        self._auto_save_bank(data)
        QMessageBox.information(self, "Đã lưu", "Cấu hình tài khoản ngân hàng đã được lưu.")

    def _auto_save_bank(self, data: dict):
        """Silently persist bank settings to disk (no popup)."""
        try:
            self._BANK_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self._BANK_CFG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

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
