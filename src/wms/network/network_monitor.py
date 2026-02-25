"""
Network Monitor - Detects network changes and triggers server restart.

Monitors:
  - Network interface changes (WiFi disconnect/reconnect)
  - Server port availability
  - Auto-restart notification + discovery servers on failure

Supports interfaces: WiFi, Ethernet, and other network adapters.
"""

import socket
import time
from typing import Callable, Optional

import psutil
from PyQt6.QtCore import QThread, pyqtSignal


# Known interface patterns for detection
INTERFACE_PATTERNS = {
    "wifi": ["Wi-Fi", "wlan", "WLAN", "Wireless"],
    "ethernet": ["Ethernet", "eth", "Local Area Connection"],
}


def get_active_interfaces() -> dict[str, list[str]]:
    """
    Return a mapping of interface_type -> list of IPs.

    Categories: wifi, ethernet, usb_tether, hotspot, other
    """
    result: dict[str, list[str]] = {
        "wifi": [],
        "ethernet": [],
        "other": [],
    }

    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface_name, addr_list in addrs.items():
            # Skip interfaces that are down
            if iface_name in stats and not stats[iface_name].isup:
                continue

            for addr in addr_list:
                if addr.family != socket.AF_INET:
                    continue
                ip = addr.address
                if ip.startswith("127.") or ip == "0.0.0.0":
                    continue

                # Classify interface
                classified = False
                for itype, patterns in INTERFACE_PATTERNS.items():
                    for pattern in patterns:
                        if pattern.lower() in iface_name.lower():
                            result[itype].append(ip)
                            classified = True
                            break
                    if classified:
                        break

                if not classified:
                    result["other"].append(ip)

    except Exception:
        pass

    return result


def get_best_ip() -> tuple[str, str]:
    """
    Return (ip, interface_type) for the best available interface.

    Priority: wifi > ethernet > usb_tether > hotspot > other > loopback
    """
    interfaces = get_active_interfaces()

    priority = ["wifi", "ethernet", "other"]
    for itype in priority:
        if interfaces.get(itype):
            return interfaces[itype][0], itype

    return "127.0.0.1", "loopback"


def get_all_ips_flat() -> list[str]:
    """Return all non-loopback IPs across all interfaces."""
    interfaces = get_active_interfaces()
    ips = []
    for ip_list in interfaces.values():
        ips.extend(ip_list)
    return list(dict.fromkeys(ips))  # deduplicate preserving order


class NetworkMonitor(QThread):
    """
    Background thread that monitors network state changes.

    Signals:
        network_changed(dict):  Emitted when interfaces change.
                                Payload: {"ips": [...], "best_ip": str,
                                          "best_type": str, "interfaces": dict}
        server_down():          Emitted when the notification server port
                                is unreachable (self-check).
        network_lost():         Emitted when ALL network interfaces are gone.
        network_restored(str):  Emitted when network comes back (best_ip).
    """

    network_changed = pyqtSignal(dict)
    server_down = pyqtSignal()
    network_lost = pyqtSignal()
    network_restored = pyqtSignal(str)

    def __init__(
        self,
        check_interval: float = 5.0,
        server_port: int = 5005,
        logger=None,
        parent=None,
    ):
        super().__init__(parent)
        self._interval = check_interval
        self._server_port = server_port
        self.logger = logger
        self._running = False

        # Cached state
        self._last_ips: set[str] = set()
        self._was_online = True
        self._consecutive_server_fails = 0
        self._max_server_fails = 3  # Emit server_down after 3 consecutive failures

    def run(self):
        self._running = True
        # Initial snapshot
        self._last_ips = set(get_all_ips_flat())
        self._was_online = len(self._last_ips) > 0

        if self.logger:
            self.logger.info(
                f"NetworkMonitor started (interval={self._interval}s, "
                f"port={self._server_port}, IPs={list(self._last_ips)})"
            )

        while self._running:
            try:
                self._check_network()
                self._check_server_port()
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"NetworkMonitor check error: {e}")

            # Sleep in small chunks so stop() is responsive
            for _ in range(int(self._interval * 10)):
                if not self._running:
                    break
                time.sleep(0.1)

    def stop(self):
        self._running = False

    # ── Internal checks ─────────────────────────────────────────

    def _check_network(self):
        """Detect IP changes (WiFi reconnect, interface added/removed)."""
        current_ips = set(get_all_ips_flat())
        is_online = len(current_ips) > 0

        # Network lost
        if self._was_online and not is_online:
            self._was_online = False
            if self.logger:
                self.logger.warning("NetworkMonitor: All network interfaces lost!")
            self.network_lost.emit()
            self._last_ips = current_ips
            return

        # Network restored
        if not self._was_online and is_online:
            self._was_online = True
            best_ip, best_type = get_best_ip()
            if self.logger:
                self.logger.info(
                    f"NetworkMonitor: Network restored → {best_ip} ({best_type})"
                )
            self.network_restored.emit(best_ip)
            self._last_ips = current_ips
            return

        # IP changed (e.g. switched from WiFi to Ethernet)
        if current_ips != self._last_ips and is_online:
            best_ip, best_type = get_best_ip()
            interfaces = get_active_interfaces()
            if self.logger:
                added = current_ips - self._last_ips
                removed = self._last_ips - current_ips
                self.logger.info(
                    f"NetworkMonitor: IPs changed "
                    f"(+{list(added) if added else '[]'}, "
                    f"-{list(removed) if removed else '[]'}) "
                    f"→ best={best_ip} ({best_type})"
                )
            self.network_changed.emit(
                {
                    "ips": list(current_ips),
                    "best_ip": best_ip,
                    "best_type": best_type,
                    "interfaces": interfaces,
                }
            )
            self._last_ips = current_ips

    def _check_server_port(self):
        """Self-check: can we connect to our own notification server?"""
        if not self._was_online:
            return  # No point checking if network is down

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("127.0.0.1", self._server_port))
            sock.close()

            if result == 0:
                self._consecutive_server_fails = 0
            else:
                self._consecutive_server_fails += 1
                if self._consecutive_server_fails >= self._max_server_fails:
                    if self.logger:
                        self.logger.warning(
                            f"NetworkMonitor: Server port {self._server_port} "
                            f"unreachable ({self._consecutive_server_fails} failures)"
                        )
                    self.server_down.emit()
                    self._consecutive_server_fails = 0  # Reset to avoid spamming
        except Exception:
            self._consecutive_server_fails += 1
