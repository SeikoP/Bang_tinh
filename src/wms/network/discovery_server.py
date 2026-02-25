"""
UDP Discovery Server - Allows Android app to find PC without knowing IP.

Protocol:
  Android sends UDP broadcast: "WMS_DISCOVER" → port 5006
  PC responds with JSON:       {"h": "192.168.1.x", "p": 5005, "k": "secret"}

This way Android only needs to be on the same WiFi network.
"""

import json
import socket
import struct

from PyQt6.QtCore import QThread, pyqtSignal


DISCOVERY_PORT = 5006
DISCOVERY_MSG = b"WMS_DISCOVER"


def get_all_local_ips() -> list[str]:
    """Return all non-loopback IPv4 addresses for this machine."""
    ips = []
    try:
        hostname = socket.gethostname()
        infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
        for info in infos:
            ip = info[4][0]
            if not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    # Fallback: connect trick to find primary IP
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
            s.close()
        except Exception:
            pass

    return list(dict.fromkeys(ips))  # deduplicate preserving order


class DiscoveryServer(QThread):
    """
    UDP server that responds to Android discovery broadcasts.

    Android sends: "WMS_DISCOVER" as UDP to broadcast address
    PC responds:   {"h": "<local_ip>", "p": 5005, "k": "<secret_key>"}
    """

    client_discovered = pyqtSignal(str)

    def __init__(self, http_port: int = 5005, logger=None, container=None):
        super().__init__()
        self.http_port = http_port
        self.logger = logger
        self.container = container
        self._sock: socket.socket | None = None
        self._running = False

    def run(self):
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock.settimeout(1.0)  # 1s timeout so stop() works quickly
            self._sock.bind(("", DISCOVERY_PORT))

            # Get secret key
            secret_key = self._get_secret_key()

            if self.logger:
                self.logger.info(f"Discovery Server listening on UDP:{DISCOVERY_PORT}")

            while self._running:
                try:
                    data, addr = self._sock.recvfrom(256)
                    if data.strip() == DISCOVERY_MSG:
                        # Determine which local IP to report
                        ips = get_all_local_ips()
                        primary_ip = ips[0] if ips else "127.0.0.1"

                        response = json.dumps({
                            "h": primary_ip,
                            "p": self.http_port,
                            "k": secret_key,
                            "ips": ips,
                        }).encode("utf-8")

                        self._sock.sendto(response, addr)

                        if self.logger:
                            self.logger.info(
                                f"Discovery: responded to {addr[0]} → {primary_ip}:{self.http_port}"
                            )
                        self.client_discovered.emit(addr[0])

                except socket.timeout:
                    continue  # normal — lets us check _running
                except OSError:
                    break

        except OSError as e:
            if self.logger:
                self.logger.warning(
                    f"Discovery Server could not bind UDP:{DISCOVERY_PORT}: {e}"
                )
        finally:
            self._cleanup()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

    def _cleanup(self):
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self.logger:
            self.logger.info("Discovery Server stopped")

    def _get_secret_key(self) -> str:
        try:
            if self.container:
                config = self.container.get("config")
                if config:
                    return config.secret_key
        except Exception:
            pass
        # Fallback: read from env
        from ..core.config import Config
        return Config.from_env().secret_key
