"""
Notification Server - Background thread for receiving notifications
"""

from http.server import ThreadingHTTPServer
from PyQt6.QtCore import QThread, pyqtSignal

from network.notification_handler import NotificationHandler


class NotificationServer(QThread):
    """Luồng chạy server lắng nghe thông báo"""

    msg_received = pyqtSignal(str)

    def __init__(self, host="0.0.0.0", port=5005, logger=None):
        super().__init__()
        self.host = host
        self.port = port
        self.logger = logger
        self._server = None
        self._running = False

    def run(self):
        try:
            # Sử dụng ThreadingHTTPServer để xử lý đa luồng
            self._server = ThreadingHTTPServer((self.host, self.port), NotificationHandler)
            self._server.allow_reuse_address = True
            self._server.timeout = 5
            self._server.signal = self.msg_received
            self._server.logger = self.logger
            
            # --- AUTH CONFIG ---
            from core.config import Config
            self.secret_key = Config.from_env().secret_key
            self._server.secret_key = self.secret_key
            
            if self.logger:
                self.logger.info(f"Notification Server started on {self.host}:{self.port}")
                self.logger.info(f"Using Secret Key for Authentication: {self.secret_key[:8]}...")
            
            # Serve forever with proper shutdown handling
            while self._running:
                self._server.handle_request()
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not start server: {e}")
        finally:
            self.cleanup()

    def stop(self):
        """Stop the server gracefully"""
        self._running = False
        if self._server:
            try:
                self._server.shutdown()
            except:
                pass

    def cleanup(self):
        """Cleanup server resources"""
        if self._server:
            try:
                self._server.server_close()
            except:
                pass
            self._server = None
        
        if self.logger:
            self.logger.info("Notification Server stopped")
