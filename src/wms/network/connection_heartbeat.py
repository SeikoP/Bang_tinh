"""
Connection Heartbeat - Tracks Android device connectivity via activity-based detection.

Features:
  - Tracks connected Android clients by monitoring their HTTP activity
  - Detects online/offline based on last communication time (not TCP ping)
  - Emits signals when a device goes offline/online
  - Provides connection quality metrics (latency, packet loss)

The Android phone sends HTTP requests (notifications, pings) to the PC server.
We track the last time each device communicated to determine online/offline status.
"""

import json
import socket
import time
from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtCore import QThread, QTimer, pyqtSignal


# Timeout: if no activity from device for this many seconds, mark offline
ACTIVITY_OFFLINE_TIMEOUT = 45  # ~1.5x the Android check interval (30s)


@dataclass
class DeviceInfo:
    """Tracked Android device."""
    ip: str
    port: int = 5005
    last_seen: float = 0.0
    last_latency_ms: float = 0.0
    consecutive_failures: int = 0
    total_pings: int = 0
    successful_pings: int = 0
    is_online: bool = False
    name: str = ""

    @property
    def packet_loss_pct(self) -> float:
        if self.total_pings == 0:
            return 0.0
        return round((1 - self.successful_pings / self.total_pings) * 100, 1)

    @property
    def age_seconds(self) -> float:
        if self.last_seen == 0:
            return float("inf")
        return time.time() - self.last_seen


class ConnectionHeartbeat(QThread):
    """
    Background thread that monitors Android device connectivity.

    Instead of TCP-pinging the phone (which has no listening port),
    this tracks when the phone last sent an HTTP request to our server.
    If no activity is seen within ACTIVITY_OFFLINE_TIMEOUT seconds,
    the device is marked offline.

    Signals:
        device_online(str, float):   (ip, latency_ms)
        device_offline(str):         ip of device that went offline
        device_discovered(str):      ip of newly tracked device
        status_update(dict):         Full status for UI display
    """

    device_online = pyqtSignal(str, float)
    device_offline = pyqtSignal(str)
    device_discovered = pyqtSignal(str)
    status_update = pyqtSignal(dict)

    # Forget devices not seen for 1 hour
    EXPIRY_SECONDS = 3600

    def __init__(
        self,
        ping_interval: float = 10.0,
        server_port: int = 5005,
        secret_key: str = "",
        logger=None,
        parent=None,
    ):
        super().__init__(parent)
        self._interval = ping_interval
        self._server_port = server_port
        self._secret_key = secret_key
        self.logger = logger
        self._running = False
        self._devices: dict[str, DeviceInfo] = {}

    # ── Public API ──────────────────────────────────────────────

    def add_device(self, ip: str, port: int = 5005, name: str = ""):
        """Register a device for heartbeat tracking."""
        if ip not in self._devices:
            self._devices[ip] = DeviceInfo(ip=ip, port=port, name=name)
            if self.logger:
                self.logger.info(f"Heartbeat: tracking device {ip}:{port}")
            self.device_discovered.emit(ip)
        else:
            # Update port/name if provided
            dev = self._devices[ip]
            if port:
                dev.port = port
            if name:
                dev.name = name

    def remove_device(self, ip: str):
        """Stop tracking a device."""
        self._devices.pop(ip, None)

    def get_devices(self) -> dict[str, DeviceInfo]:
        """Return a copy of tracked devices."""
        return dict(self._devices)

    def get_online_count(self) -> int:
        return sum(1 for d in self._devices.values() if d.is_online)

    def touch_device(self, ip: str, latency_ms: float = 0.0):
        """
        Mark a device as 'just seen' — called when the PC receives
        any HTTP request from a known Android device IP.
        """
        if ip in self._devices:
            dev = self._devices[ip]
            dev.last_seen = time.time()
            dev.last_latency_ms = latency_ms
            dev.successful_pings += 1
            dev.total_pings += 1
            dev.consecutive_failures = 0
            if not dev.is_online:
                dev.is_online = True
                if self.logger:
                    self.logger.info(
                        f"Heartbeat: {ip} came ONLINE (activity-based)"
                    )
                self.device_online.emit(ip, latency_ms)
        else:
            # Auto-track new device on first HTTP contact
            self._devices[ip] = DeviceInfo(
                ip=ip,
                last_seen=time.time(),
                last_latency_ms=latency_ms,
                is_online=True,
                successful_pings=1,
                total_pings=1,
            )
            if self.logger:
                self.logger.info(f"Heartbeat: auto-tracking new device {ip}")
            self.device_discovered.emit(ip)
            self.device_online.emit(ip, latency_ms)

    # ── Thread loop ─────────────────────────────────────────────

    def run(self):
        self._running = True
        if self.logger:
            self.logger.info(
                f"ConnectionHeartbeat started (interval={self._interval}s, "
                f"offline_timeout={ACTIVITY_OFFLINE_TIMEOUT}s)"
            )

        while self._running:
            try:
                self._check_device_activity()
                self._expire_old_devices()
                self._emit_status()
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"Heartbeat error: {e}")

            # Sleep in small chunks for quick stop
            for _ in range(int(self._interval * 10)):
                if not self._running:
                    break
                time.sleep(0.1)

    def stop(self):
        self._running = False

    # ── Internal ────────────────────────────────────────────────

    def _check_device_activity(self):
        """
        Check each tracked device's last_seen time.
        If no activity within ACTIVITY_OFFLINE_TIMEOUT, mark offline.
        """
        now = time.time()
        for ip, device in list(self._devices.items()):
            if device.last_seen == 0:
                # Never seen via HTTP yet — skip
                continue

            elapsed = now - device.last_seen
            if device.is_online and elapsed > ACTIVITY_OFFLINE_TIMEOUT:
                device.is_online = False
                device.consecutive_failures += 1
                if self.logger:
                    self.logger.warning(
                        f"Heartbeat: {ip} went OFFLINE "
                        f"(no activity for {elapsed:.0f}s)"
                    )
                self.device_offline.emit(ip)

    def _expire_old_devices(self):
        """Remove devices not seen for a long time."""
        expired = [
            ip
            for ip, dev in self._devices.items()
            if dev.age_seconds > self.EXPIRY_SECONDS and not dev.is_online
        ]
        for ip in expired:
            if self.logger:
                self.logger.info(f"Heartbeat: expiring stale device {ip}")
            del self._devices[ip]

    def _emit_status(self):
        """Emit full status for UI rendering."""
        online = []
        offline = []
        for ip, dev in self._devices.items():
            info = {
                "ip": ip,
                "name": dev.name or ip,
                "latency_ms": dev.last_latency_ms,
                "packet_loss": dev.packet_loss_pct,
                "is_online": dev.is_online,
            }
            if dev.is_online:
                online.append(info)
            else:
                offline.append(info)

        self.status_update.emit(
            {
                "online_count": len(online),
                "offline_count": len(offline),
                "devices": online + offline,
            }
        )
