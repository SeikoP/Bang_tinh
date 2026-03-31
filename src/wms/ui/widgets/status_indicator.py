"""
Status Indicator Widget - Shows server connection state in sidebar
Provides visual feedback: 🟢 Running / 🔴 Stopped / 🟡 Starting
Click to open Connection Detail popup with device list & event log.
"""

import datetime
import json
import time
from collections import deque
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QDialog, QPushButton,
    QApplication, QScrollArea, QSizePolicy,
)
from PyQt6.QtGui import QPainter, QColor, QBrush

from ..theme import AppColors


def _format_elapsed(seconds: float) -> str:
    """Human-friendly elapsed time string."""
    if seconds < 60:
        return f"{int(seconds)}s truoc"
    elif seconds < 3600:
        return f"{int(seconds // 60)} phut truoc"
    else:
        return f"{int(seconds // 3600)}h truoc"


class StatusDot(QWidget):
    """Animated colored circle for status indication"""

    def __init__(self, size=8, parent=None):
        super().__init__(parent)
        self._color = QColor("#22c55e")
        self._size = size
        self.setFixedSize(size + 4, size + 4)

    def set_color(self, color: str):
        self._color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Glow
        glow = QColor(self._color)
        glow.setAlpha(60)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self._size + 4, self._size + 4)
        # Dot
        painter.setBrush(QBrush(self._color))
        painter.drawEllipse(2, 2, self._size, self._size)
        painter.end()


# ─────────────────────────────────────────────────────────────────
# Connection Detail Popup
# ─────────────────────────────────────────────────────────────────
class ConnectionDetailDialog(QDialog):
    """Popup showing all connection details when clicking the status dot."""

    _CHECK_LABELS = {
        "server": "HTTP Server",
        "auth": "Xac thuc (Auth)",
        "database": "Co so du lieu",
        "signal": "Signal Bridge",
    }

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chi tiet ket noi")
        self.setFixedWidth(480)
        self._info = info
        self.setStyleSheet(f"""
            QDialog {{
                background: {AppColors.BG_SECONDARY};
                border-radius: 12px;
            }}
        """)
        self._build_ui()

    # ── helpers ─────────────────────────────────────────────────

    @staticmethod
    def _card(parent_layout) -> QVBoxLayout:
        """Create a rounded card frame and return its inner layout."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {AppColors.SURFACE};
                border: 1px solid {AppColors.BORDER};
                border-radius: 10px;
            }}
        """)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(8)
        parent_layout.addWidget(card)
        return inner

    @staticmethod
    def _section_title(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"""
            font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
            color: {AppColors.TEXT_SECONDARY}; text-transform: uppercase;
            background: transparent; border: none;
        """)
        return lbl

    @staticmethod
    def _info_row(key: str, val: str, mono: bool = False) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        k = QLabel(key)
        k.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;
            background: transparent; border: none;
        """)
        k.setFixedWidth(110)
        v = QLabel(val)
        font_family = "'Consolas', 'Courier New', monospace" if mono else "'Roboto', sans-serif"
        v.setStyleSheet(f"""
            color: {AppColors.TEXT}; font-size: 12px; font-weight: 600;
            font-family: {font_family}; background: transparent; border: none;
        """)
        v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.setWordWrap(True)
        row.addWidget(k)
        row.addWidget(v, 1)
        return row

    # ── main build ─────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        # ── Status banner ──────────────────────────────────────
        state = self._info.get("state", "stopped")
        color = self._info.get("state_color", "#ef4444")
        label = self._info.get("state_label", "Server: OFF")

        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background: {color};
                border-radius: 10px;
                border: none;
            }}
        """)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(16, 12, 16, 12)
        banner_lay.setSpacing(10)

        dot = StatusDot(size=10)
        dot.set_color("#FFFFFF")
        banner_lay.addWidget(dot)

        status_text = QLabel(label)
        status_text.setStyleSheet("""
            color: white; font-size: 15px; font-weight: 800;
            letter-spacing: 0.02em; background: transparent; border: none;
        """)
        banner_lay.addWidget(status_text)
        banner_lay.addStretch()

        conn_type = self._info.get("connection_type", "")
        if conn_type and conn_type != "—":
            type_badge = QLabel(conn_type)
            type_badge.setStyleSheet("""
                background: rgba(255,255,255,0.25); color: white;
                font-size: 10px; font-weight: 700; padding: 3px 10px;
                border-radius: 10px; border: none;
            """)
            banner_lay.addWidget(type_badge)

        root.addWidget(banner)

        # ── Network info card ──────────────────────────────────
        net_inner = self._card(root)
        net_inner.addWidget(self._section_title("THONG TIN MANG"))

        ip = self._info.get("ip", "—")
        port = str(self._info.get("port", "—"))
        net_inner.addLayout(self._info_row("Dia chi IP", ip, mono=True))
        net_inner.addLayout(self._info_row("Cong (Port)", port, mono=True))
        net_inner.addLayout(self._info_row(
            "Secret Key", self._info.get("secret_key_short", "—"), mono=True
        ))

        # All IPs
        all_ips = self._info.get("all_ips", [])
        if len(all_ips) > 1:
            net_inner.addLayout(self._info_row(
                "Tat ca IP", ", ".join(all_ips), mono=True
            ))

        # ── Devices card ───────────────────────────────────────
        devices = self._info.get("devices", [])
        dev_inner = self._card(root)
        online_count = sum(1 for d in devices if d.get("is_online"))
        offline_count = sum(1 for d in devices if not d.get("is_online"))
        title_suffix = f" — {online_count} online"
        if offline_count:
            title_suffix += f", {offline_count} offline"
        dev_inner.addWidget(self._section_title(f"THIET BI{title_suffix}"))

        if devices:
            for dev in devices:
                self._build_device_row(dev_inner, dev)
        else:
            empty = QLabel("Chua co thiet bi nao ket noi")
            empty.setStyleSheet(f"""
                color: {AppColors.TEXT_SECONDARY}; font-size: 11px;
                font-style: italic; background: transparent; border: none;
            """)
            dev_inner.addWidget(empty)

        # ── Tunnel card ────────────────────────────────────────
        tunnel_url = self._info.get("tunnel_url", "Khong co")
        has_tunnel = tunnel_url not in ("Khong co", "", "—")

        tun_inner = self._card(root)
        tun_inner.addWidget(self._section_title("CLOUDFLARE TUNNEL"))

        tun_row = QHBoxLayout()
        tun_row.setSpacing(8)

        tun_dot = StatusDot(size=6)
        tun_dot.set_color(AppColors.PRIMARY if has_tunnel else "#9CA3AF")
        tun_row.addWidget(tun_dot)

        tun_status = QLabel("Dang hoat dong" if has_tunnel else "Khong kich hoat")
        tun_status_color = AppColors.PRIMARY if has_tunnel else AppColors.TEXT_SECONDARY
        tun_status.setStyleSheet(f"""
            color: {tun_status_color}; font-size: 12px; font-weight: 600;
            background: transparent; border: none;
        """)
        tun_row.addWidget(tun_status)
        tun_row.addStretch()

        if has_tunnel:
            copy_tun_btn = QPushButton("Copy URL")
            copy_tun_btn.setFixedHeight(26)
            copy_tun_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_tun_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {AppColors.BG_HOVER}; color: {AppColors.TEXT};
                    border: 1px solid {AppColors.BORDER}; border-radius: 5px;
                    font-size: 10px; font-weight: 600; padding: 0 10px;
                }}
                QPushButton:hover {{
                    background: {AppColors.PRIMARY}; color: white;
                    border-color: {AppColors.PRIMARY};
                }}
            """)
            copy_tun_btn.clicked.connect(
                lambda: QApplication.clipboard().setText(tunnel_url)
            )
            tun_row.addWidget(copy_tun_btn)

        tun_inner.addLayout(tun_row)

        if has_tunnel:
            url_lbl = QLabel(tunnel_url)
            url_lbl.setStyleSheet(f"""
                color: {AppColors.INFO}; font-size: 11px;
                font-family: 'Consolas', monospace;
                background: rgba(37, 99, 235, 0.06); padding: 6px 10px;
                border-radius: 6px; border: none;
            """)
            url_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            url_lbl.setWordWrap(True)
            tun_inner.addWidget(url_lbl)

        # ── Health checks card ─────────────────────────────────
        checks = self._info.get("server_checks")
        chk_inner = self._card(root)
        chk_inner.addWidget(self._section_title("KIEM TRA HE THONG"))

        if checks:
            all_ok = all(checks.values())
            summary_color = AppColors.PRIMARY if all_ok else AppColors.ERROR
            summary_text = "Tat ca binh thuong" if all_ok else "Co loi can xu ly"
            summary = QLabel(summary_text)
            summary.setStyleSheet(f"""
                color: {summary_color}; font-size: 11px; font-weight: 700;
                background: transparent; border: none; margin-bottom: 2px;
            """)
            chk_inner.addWidget(summary)

            for name, ok in checks.items():
                display_name = self._CHECK_LABELS.get(name, name.capitalize())
                chk_row = QHBoxLayout()
                chk_row.setSpacing(8)

                chk_dot = StatusDot(size=6)
                chk_dot.set_color(AppColors.PRIMARY if ok else AppColors.ERROR)
                chk_row.addWidget(chk_dot)

                chk_name = QLabel(display_name)
                chk_name.setStyleSheet(f"""
                    color: {AppColors.TEXT}; font-size: 12px; font-weight: 500;
                    background: transparent; border: none;
                """)
                chk_row.addWidget(chk_name, 1)

                chk_badge = QLabel("OK" if ok else "LOI")
                badge_bg = "rgba(16,185,129,0.1)" if ok else "rgba(220,38,38,0.1)"
                badge_color = AppColors.PRIMARY if ok else AppColors.ERROR
                chk_badge.setStyleSheet(f"""
                    background: {badge_bg}; color: {badge_color};
                    font-size: 10px; font-weight: 700; padding: 2px 8px;
                    border-radius: 4px; border: none;
                """)
                chk_badge.setFixedHeight(20)
                chk_row.addWidget(chk_badge)

                chk_inner.addLayout(chk_row)

            errors = self._info.get("server_errors")
            if errors:
                for err in errors:
                    e_lbl = QLabel(f"  {err}")
                    e_lbl.setWordWrap(True)
                    e_lbl.setStyleSheet(f"""
                        font-size: 11px; color: {AppColors.ERROR};
                        background: rgba(220,38,38,0.06); padding: 4px 8px;
                        border-radius: 4px; border: none;
                    """)
                    chk_inner.addWidget(e_lbl)
        else:
            no_chk = QLabel("Khong kiem tra duoc (server chua chay?)")
            no_chk.setStyleSheet(f"""
                color: {AppColors.TEXT_SECONDARY}; font-size: 11px;
                font-style: italic; background: transparent; border: none;
            """)
            chk_inner.addWidget(no_chk)

        # ── Connection event log ───────────────────────────────
        events = self._info.get("connection_events", [])
        if events:
            log_inner = self._card(root)
            log_inner.addWidget(self._section_title("LICH SU KET NOI"))
            for ev in events[:15]:  # show last 15
                ev_row = QHBoxLayout()
                ev_row.setSpacing(6)

                ev_icon = QLabel(ev.get("icon", "•"))
                ev_icon.setFixedWidth(16)
                ev_icon.setStyleSheet("""
                    font-size: 11px; background: transparent; border: none;
                """)
                ev_row.addWidget(ev_icon)

                ev_text = QLabel(ev.get("text", ""))
                ev_text.setStyleSheet(f"""
                    color: {AppColors.TEXT}; font-size: 11px;
                    background: transparent; border: none;
                """)
                ev_row.addWidget(ev_text, 1)

                ev_time = QLabel(ev.get("time", ""))
                ev_time.setStyleSheet(f"""
                    color: {AppColors.TEXT_SECONDARY}; font-size: 10px;
                    font-family: 'Consolas', monospace;
                    background: transparent; border: none;
                """)
                ev_row.addWidget(ev_time)

                log_inner.addLayout(ev_row)

        # ── Last notification ──────────────────────────────────
        last_notif = self._info.get("last_notification", "Chua co")
        notif_row = QHBoxLayout()
        notif_row.setContentsMargins(4, 0, 4, 0)
        notif_k = QLabel("Thong bao cuoi:")
        notif_k.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY}; font-size: 11px;
            background: transparent; border: none;
        """)
        notif_v = QLabel(last_notif)
        notif_v.setStyleSheet(f"""
            color: {AppColors.TEXT}; font-size: 11px; font-weight: 600;
            background: transparent; border: none;
        """)
        notif_row.addWidget(notif_k)
        notif_row.addWidget(notif_v, 1)
        root.addLayout(notif_row)

        # ── Button row ─────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.setContentsMargins(0, 2, 0, 0)

        copy_btn = QPushButton("Copy IP:Port")
        copy_btn.setFixedHeight(36)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY}; color: white; border: none;
                border-radius: 8px; font-weight: 700; font-size: 12px; padding: 0 18px;
            }}
            QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
        """)
        copy_btn.clicked.connect(self._copy_address)
        btn_row.addWidget(copy_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Dong")
        close_btn.setFixedHeight(36)
        close_btn.setFixedWidth(80)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.BG_HOVER}; color: {AppColors.TEXT};
                border: 1px solid {AppColors.BORDER}; border-radius: 8px;
                font-weight: 600; font-size: 12px;
            }}
            QPushButton:hover {{
                background: {AppColors.BORDER}; border-color: {AppColors.BORDER_HOVER};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    def _build_device_row(self, parent_layout: QVBoxLayout, dev: dict):
        """Build a single device row with status details."""
        is_online = dev.get("is_online", False)
        ip = dev.get("ip", "?")
        name = dev.get("name", ip)
        latency = dev.get("latency_ms", 0)
        packet_loss = dev.get("packet_loss", 0)
        last_seen = dev.get("last_seen_ago", "")

        # Device card row
        row_frame = QFrame()
        bg = "rgba(16,185,129,0.06)" if is_online else "rgba(220,38,38,0.04)"
        border_color = "rgba(16,185,129,0.2)" if is_online else "rgba(220,38,38,0.15)"
        row_frame.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)
        row_lay = QVBoxLayout(row_frame)
        row_lay.setContentsMargins(12, 8, 12, 8)
        row_lay.setSpacing(4)

        # Top line: dot + name + status badge
        top = QHBoxLayout()
        top.setSpacing(8)

        d = StatusDot(size=8)
        d.set_color(AppColors.PRIMARY if is_online else AppColors.ERROR)
        top.addWidget(d)

        name_lbl = QLabel(name if name != ip else ip)
        name_lbl.setStyleSheet(f"""
            color: {AppColors.TEXT}; font-size: 12px; font-weight: 700;
            background: transparent; border: none;
        """)
        top.addWidget(name_lbl)
        top.addStretch()

        status_lbl = QLabel("Online" if is_online else "Offline")
        sc = AppColors.PRIMARY if is_online else AppColors.ERROR
        sbg = "rgba(16,185,129,0.12)" if is_online else "rgba(220,38,38,0.12)"
        status_lbl.setStyleSheet(f"""
            background: {sbg}; color: {sc};
            font-size: 10px; font-weight: 700; padding: 2px 8px;
            border-radius: 4px; border: none;
        """)
        status_lbl.setFixedHeight(20)
        top.addWidget(status_lbl)

        row_lay.addLayout(top)

        # Bottom line: IP | latency | packet loss | last seen
        details = QHBoxLayout()
        details.setSpacing(12)

        ip_lbl = QLabel(f"IP: {ip}")
        ip_lbl.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY}; font-size: 10px;
            font-family: 'Consolas', monospace;
            background: transparent; border: none;
        """)
        details.addWidget(ip_lbl)

        if is_online and latency > 0:
            lat_color = AppColors.PRIMARY if latency < 50 else ("#f59e0b" if latency < 200 else AppColors.ERROR)
            lat_lbl = QLabel(f"⏱ {latency:.0f}ms")
            lat_lbl.setStyleSheet(f"""
                color: {lat_color}; font-size: 10px; font-weight: 600;
                background: transparent; border: none;
            """)
            details.addWidget(lat_lbl)

        if packet_loss > 0:
            pl_lbl = QLabel(f"📉 {packet_loss:.1f}% mat")
            pl_lbl.setStyleSheet(f"""
                color: {AppColors.ERROR}; font-size: 10px;
                background: transparent; border: none;
            """)
            details.addWidget(pl_lbl)

        if last_seen:
            ls_lbl = QLabel(f"Lan cuoi: {last_seen}")
            ls_lbl.setStyleSheet(f"""
                color: {AppColors.TEXT_SECONDARY}; font-size: 10px;
                background: transparent; border: none;
            """)
            details.addWidget(ls_lbl)

        details.addStretch()
        row_lay.addLayout(details)

        parent_layout.addWidget(row_frame)

    def _copy_address(self):
        ip = self._info.get("ip", "")
        port = self._info.get("port", 5005)
        QApplication.clipboard().setText(f"{ip}:{port}")


# ─────────────────────────────────────────────────────────────────
# Status Indicator
# ─────────────────────────────────────────────────────────────────
class StatusIndicator(QFrame):
    """
    Server status indicator widget for sidebar.

    States:
        - RUNNING (green): Server is accepting connections
        - STOPPED (red): Server is not running
        - STARTING (yellow): Server is initializing
        - NO_DATA (amber): Running but no recent notifications
    """

    clicked = pyqtSignal()

    STATE_RUNNING = "running"
    STATE_STOPPED = "stopped"
    STATE_STARTING = "starting"
    STATE_NO_DATA = "no_data"
    STATE_NO_NETWORK = "no_network"
    STATE_RECONNECTING = "reconnecting"

    _COLORS = {
        STATE_RUNNING: "#22c55e",
        STATE_STOPPED: "#ef4444",
        STATE_STARTING: "#f59e0b",
        STATE_NO_DATA: "#f97316",
        STATE_NO_NETWORK: "#dc2626",
        STATE_RECONNECTING: "#a855f7",
    }

    _LABELS = {
        STATE_RUNNING: "Server: ON",
        STATE_STOPPED: "Server: OFF",
        STATE_STARTING: "Starting...",
        STATE_NO_DATA: "No data",
        STATE_NO_NETWORK: "No network",
        STATE_RECONNECTING: "Reconnecting...",
    }

    _INTERFACE_LABELS = {
        "wifi": "WiFi",
        "ethernet": "LAN",
        "loopback": "Local",
        "other": "Network",
    }

    # Max events to keep in the log
    _MAX_EVENTS = 50

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = self.STATE_STARTING
        self._last_notification_time = None
        self._no_data_threshold_ms = 600_000  # 10 minutes
        self._connection_type = ""
        self._device_count = 0
        self._last_heartbeat_status: dict = {}
        self._connection_events: deque = deque(maxlen=self._MAX_EVENTS)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self._dot = StatusDot(size=8)
        layout.addWidget(self._dot)

        self._label = QLabel(self._LABELS[self._state])
        self._label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 10px;
                font-weight: 600;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self._label)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.45);
                font-size: 9px;
                background: transparent;
                border: none;
            }
        """)
        layout.addWidget(self._info_label)
        layout.addStretch()

        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 6px;
                border: none;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click de xem chi tiet ket noi")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    # ── State management ──────────────────────────────────────

    def set_state(self, state: str):
        if state == self._state:
            return
        self._state = state
        color = self._COLORS.get(state, self._COLORS[self.STATE_STOPPED])
        label = self._LABELS.get(state, "Unknown")
        self._dot.set_color(color)
        self._label.setText(label)
        self._update_info()

    def set_connection_type(self, conn_type: str):
        self._connection_type = conn_type
        self._update_info()

    def set_device_count(self, count: int):
        self._device_count = count
        self._update_info()

    def update_heartbeat_status(self, status: dict):
        """Store latest heartbeat status for use in the detail dialog."""
        self._last_heartbeat_status = status

    def log_connection_event(self, icon: str, text: str):
        """Append a connection event to the log (shown in dialog)."""
        now = datetime.datetime.now()
        self._connection_events.appendleft({
            "icon": icon,
            "text": text,
            "time": now.strftime("%H:%M:%S"),
        })

    def _update_info(self):
        parts = []
        if self._connection_type:
            display = self._INTERFACE_LABELS.get(
                self._connection_type, self._connection_type
            )
            parts.append(display)
        if self._device_count > 0:
            parts.append(f"{self._device_count} device{'s' if self._device_count > 1 else ''}")
        self._info_label.setText(" · ".join(parts))

    def record_notification(self):
        self._last_notification_time = int(time.time() * 1000)

    def check_no_data(self):
        if self._state != self.STATE_RUNNING:
            return
        if self._last_notification_time is None:
            return
        now = int(time.time() * 1000)
        elapsed = now - self._last_notification_time
        if elapsed > self._no_data_threshold_ms:
            self.set_state(self.STATE_NO_DATA)
        elif self._state == self.STATE_NO_DATA:
            self.set_state(self.STATE_RUNNING)

    # ── Info gathering (for popup) ────────────────────────────

    def gather_info(self, container=None, heartbeat=None) -> dict:
        """Collect all connection info for the detail popup."""
        info = {
            "state": self._state,
            "state_color": self._COLORS.get(self._state, "#ef4444"),
            "state_label": self._LABELS.get(self._state, "Unknown"),
            "connection_type": self._INTERFACE_LABELS.get(
                self._connection_type, self._connection_type or "—"
            ),
            "device_count": self._device_count,
            "ip": "—",
            "port": 5005,
            "secret_key_short": "—",
            "tunnel_url": "Khong co",
            "last_notification": "Chua co",
            "devices": [],
            "all_ips": [],
            "connection_events": list(self._connection_events),
        }

        # Last notification time
        if self._last_notification_time:
            dt = datetime.datetime.fromtimestamp(self._last_notification_time / 1000)
            elapsed_s = (int(time.time() * 1000) - self._last_notification_time) / 1000
            info["last_notification"] = f"{dt.strftime('%H:%M:%S')} ({_format_elapsed(elapsed_s)})"

        # From container
        if container:
            config = container.get("config")
            if config:
                info["port"] = config.notification_port
                key = config.secret_key or ""
                info["secret_key_short"] = (key[:8] + "..." + key[-4:]) if len(key) > 12 else key

        # IP
        try:
            from ...network.network_monitor import get_best_ip, get_all_ips_flat
            best_ip, _ = get_best_ip()
            info["ip"] = best_ip
            info["all_ips"] = get_all_ips_flat()
        except Exception:
            pass

        # Device list from heartbeat
        if heartbeat:
            now = time.time()
            devices_data = []
            devs = heartbeat.get_devices()
            for ip, dev in devs.items():
                last_seen_ago = ""
                if dev.last_seen > 0:
                    last_seen_ago = _format_elapsed(now - dev.last_seen)
                devices_data.append({
                    "ip": dev.ip,
                    "name": dev.name or dev.ip,
                    "is_online": dev.is_online,
                    "latency_ms": dev.last_latency_ms,
                    "packet_loss": dev.packet_loss_pct,
                    "last_seen_ago": last_seen_ago,
                    "total_pings": dev.total_pings,
                    "successful_pings": dev.successful_pings,
                })
            # Sort: online first
            devices_data.sort(key=lambda d: (not d["is_online"], d["ip"]))
            info["devices"] = devices_data
            info["device_count"] = sum(1 for d in devices_data if d["is_online"])

        # Tunnel URL from state file
        try:
            tunnel_path = Path(__file__).parents[3] / "config" / "tunnel_state.json"
            if tunnel_path.exists():
                data = json.loads(tunnel_path.read_text(encoding="utf-8"))
                url = data.get("tunnel_url", "")
                if url:
                    info["tunnel_url"] = url
        except Exception:
            pass

        # Server checks — run a quick self-ping
        info["server_checks"] = None
        info["server_errors"] = None
        try:
            import urllib.request
            port = info["port"]
            if container:
                config = container.get("config")
                key = config.secret_key if config else ""
            else:
                key = ""
            url = f"http://127.0.0.1:{port}/api/ping?key={key}"
            with urllib.request.urlopen(url, timeout=2) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                info["server_checks"] = result.get("checks")
                info["server_errors"] = result.get("errors")
        except Exception:
            pass

        return info
