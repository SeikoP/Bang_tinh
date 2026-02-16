import pytest
import threading
import time
import requests
from network.notification_server import NotificationServer
from core.config import Config

class TestServer:
    def __init__(self, port=5005):
        self.port = port
        self.config = Config.from_env()
        self.config.notification_port = port
        self.server = NotificationServer(host="localhost", port=port)
        # We need to start the QThread properly
        # Since we are not in a Qt event loop in this fixture, we can just call run directly in a thread
        # But QThread.start() spawns a thread.
        # If we just call server.start(), it uses QThread mechanism.
        # But QThread might require QApp.
        # Let's try calling run() directly in our thread wrapper.
        self.thread = threading.Thread(target=self.server.run)
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
        self.server.stop()
        self.thread.join(timeout=2)

@pytest.fixture(scope="module")
def http_server():
    server = TestServer(port=5005)
    try:
        server.start()
        yield server
    finally:
        server.stop()
