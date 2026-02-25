"""
Notification Server - Background thread for receiving notifications
"""

from http.server import ThreadingHTTPServer

from PyQt6.QtCore import QThread, pyqtSignal

from .notification_handler import NotificationHandler


class NotificationServer(QThread):
    """Luồng chạy server lắng nghe thông báo"""

    msg_received = pyqtSignal(str)

    def __init__(self, host="0.0.0.0", port=5005, logger=None, container=None):
        super().__init__()
        self.host = host
        self.port = port
        self.logger = logger
        self.container = container
        self._server = None

    def run(self):
        try:
            self._server = ThreadingHTTPServer(
                (self.host, self.port), NotificationHandler
            )
            self._server.allow_reuse_address = True
            self._server.signal = self.msg_received
            self._server.logger = self.logger
            self._server.container = self.container

            # --- AUTH CONFIG ---
            from ..core.config import Config

            secret_key = Config.from_env().secret_key
            self._server.secret_key = secret_key

            if self.logger:
                self.logger.info(
                    f"Notification Server started on {self.host}:{self.port}"
                )
                self.logger.info(
                    f"Using Secret Key for Authentication: {secret_key[:8]}..."
                )

            # serve_forever() blocks until shutdown() is called from another thread
            self._server.serve_forever(poll_interval=0.5)

        except OSError as e:
            if self.logger:
                self.logger.error(f"Could not bind server to {self.host}:{self.port}: {e}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Notification Server error: {e}")
        finally:
            self._cleanup()

    def stop(self):
        """Stop the server gracefully"""
        if self._server:
            try:
                self._server.shutdown()
            except OSError:
                pass

    def _cleanup(self):
        """Cleanup server resources"""
        if self._server:
            try:
                self._server.server_close()
            except OSError:
                pass
            self._server = None

        if self.logger:
            self.logger.info("Notification Server stopped")
