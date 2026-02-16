import logging
import pytest
import threading
import time
import requests
from core.config import Config

class TestServer:
    def __init__(self, port=5005):
        self.port = port
        self.config = Config.from_env()
        # We use a vanilla ThreadingHTTPServer here to test the network logic
        # without needing the whole Qt application context
        from http.server import ThreadingHTTPServer
        from network.notification_handler import NotificationHandler
        
        # Configure handler class with container/logger if needed
        # NotificationHandler uses self.server.container
        
        self.server_started = threading.Event()
        
        class TestServerInternal(ThreadingHTTPServer):
            container = None
            logger = None
            signal = None
            secret_key = None
            
        self.httpd = TestServerInternal(("", port), NotificationHandler)
        self.httpd.container = None
        self.httpd.logger = logging.getLogger("test_server")
        self.httpd.secret_key = Config.from_env().secret_key
        
        self.thread = threading.Thread(target=self.httpd.serve_forever)
        self.thread.daemon = True

    def start(self):
        self.thread.start()
        # Wait for server to be ready
        for _ in range(50):
            try:
                requests.get(f"http://localhost:{self.port}", timeout=0.5)
                return
            except:
                time.sleep(0.1)
        raise RuntimeError("Server failed to start")

    def stop(self):
        self.httpd.shutdown()
        self.thread.join(timeout=2)

@pytest.fixture(scope="module")
def http_server():
    server = TestServer(port=5005)
    try:
        server.start()
        yield server
    finally:
        server.stop()
