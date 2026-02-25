"""
Ngrok Tunnel Service — auto-start ngrok tunnel from within the app.

Uses pyngrok to manage ngrok lifecycle:
  • start tunnel → get public URL
  • stop tunnel on app exit
  • emit signals so UI can react (URL ready / error)

Requires:
  pip install pyngrok
  and a free ngrok authtoken (set once via `ngrok config add-authtoken TOKEN`
  or passed to this service).
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class _NgrokWorker(QThread):
    """Background thread that starts / stops an ngrok tunnel."""

    tunnel_ready = pyqtSignal(str)   # public_url
    tunnel_error = pyqtSignal(str)   # error message
    tunnel_stopped = pyqtSignal()

    def __init__(self, port: int, authtoken: str = "", region: str = "", parent=None):
        super().__init__(parent)
        self.port = port
        self.authtoken = authtoken
        self.region = region
        self._tunnel = None
        self._should_stop = False

    # ── lifecycle ────────────────────────────────────
    def run(self):
        try:
            from pyngrok import conf, ngrok

            # Apply authtoken if provided
            if self.authtoken:
                conf.get_default().auth_token = self.authtoken

            # Apply region if provided (e.g. "ap" for Asia Pacific)
            if self.region:
                conf.get_default().region = self.region

            # Open an HTTP tunnel to the local notification server port
            self._tunnel = ngrok.connect(self.port, "http")
            public_url: str = self._tunnel.public_url

            # Prefer https
            if public_url.startswith("http://"):
                public_url = public_url.replace("http://", "https://", 1)

            logger.info("ngrok tunnel opened: %s → localhost:%s", public_url, self.port)
            self.tunnel_ready.emit(public_url)

            # Keep thread alive until stop() is called — pyngrok process runs in background
            while not self._should_stop:
                self.msleep(500)

        except ImportError:
            self.tunnel_error.emit(
                "Chưa cài pyngrok. Chạy: pip install pyngrok"
            )
        except Exception as exc:
            msg = str(exc)
            if "ERR_NGROK" in msg and "authtoken" in msg.lower():
                self.tunnel_error.emit(
                    "Thiếu authtoken ngrok.\n"
                    "Đăng ký miễn phí tại https://dashboard.ngrok.com\n"
                    "rồi dán token vào ô Authtoken bên dưới."
                )
            else:
                self.tunnel_error.emit(f"Lỗi ngrok: {msg}")
            logger.error("ngrok tunnel error: %s", exc, exc_info=True)

    def stop(self):
        """Request graceful shutdown."""
        self._should_stop = True
        try:
            from pyngrok import ngrok
            if self._tunnel:
                ngrok.disconnect(self._tunnel.public_url)
                logger.info("ngrok tunnel disconnected")
            ngrok.kill()
        except Exception as exc:
            logger.debug("ngrok cleanup: %s", exc)
        finally:
            self.tunnel_stopped.emit()


class NgrokService(QObject):
    """
    High-level service exposed to the rest of the app.

    Signals
    -------
    tunnel_started(str)  — emitted with the public HTTPS URL
    tunnel_stopped()     — emitted when tunnel is closed
    tunnel_error(str)    — emitted on any error
    """

    tunnel_started = pyqtSignal(str)
    tunnel_stopped = pyqtSignal()
    tunnel_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[_NgrokWorker] = None
        self._public_url: str = ""

    # ── public API ──────────────────────────────────
    @property
    def public_url(self) -> str:
        return self._public_url

    @property
    def is_running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def start(self, port: int, authtoken: str = "", region: str = ""):
        """Start ngrok tunnel in background thread."""
        if self.is_running:
            logger.warning("ngrok tunnel already running at %s", self._public_url)
            return

        self._worker = _NgrokWorker(port, authtoken, region)
        self._worker.tunnel_ready.connect(self._on_ready)
        self._worker.tunnel_error.connect(self._on_error)
        self._worker.tunnel_stopped.connect(self._on_stopped)
        self._worker.start()

    def stop(self):
        """Stop ngrok tunnel."""
        if self._worker:
            self._worker.stop()
            self._worker.wait(5000)
            self._worker = None
        self._public_url = ""

    # ── private slots ───────────────────────────────
    def _on_ready(self, url: str):
        self._public_url = url
        self.tunnel_started.emit(url)

    def _on_error(self, msg: str):
        self._public_url = ""
        self.tunnel_error.emit(msg)

    def _on_stopped(self):
        self._public_url = ""
        self.tunnel_stopped.emit()
