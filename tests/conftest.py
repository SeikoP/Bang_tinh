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
            rate_limit_window = 60
            rate_limit_max = 100
            
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

def test_rate_limiting(http_server):
    """Test if rate limiting works"""
    # Set a small rate limit for testing to speed it up
    http_server.httpd.rate_limit_max = 10
    http_server.httpd.rate_limit_window = 30
    
    # Get host and port from http_server fixture if possible
    base_url = f"http://localhost:{http_server.port}"
    
    # Get authentication token from config
    headers = {}
    if hasattr(http_server, "httpd") and hasattr(http_server.httpd, "secret_key"):
        token = http_server.httpd.secret_key
        if token:
            headers["Authorization"] = f"Bearer {token}"

    # Send 20 requests rapidly (should be blocked after 10)
    success_count = 0
    blocked_count = 0
    unauthorized_count = 0
    error_count = 0

    for i in range(20):
        try:
            response = requests.get(f"{base_url}/?content=test{i}", headers=headers, timeout=2)
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                blocked_count += 1
            elif response.status_code == 401:
                unauthorized_count += 1
        except Exception as e:
            error_count += 1
            if i < 3: # Log first few errors
                 print(f"Request error: {e}")

    print(f"Rate limit test: {success_count} success, {blocked_count} blocked, {unauthorized_count} unauthorized, {error_count} errors")
    
    # Should have some blocked requests
    assert blocked_count > 0, f"Rate limiting not working - blocked: {blocked_count}, success: {success_count}, unauthorized: {unauthorized_count}, errors: {error_count}"
