#!/usr/bin/env python3
"""Quick test for notification server"""
import time
import requests
import threading
from PyQt6.QtCore import QCoreApplication
from src.wms.network.notification_server import NotificationServer

def test_server():
    """Test notification server startup and basic request"""
    
    # Need Qt application for QThread
    app = QCoreApplication.instance()
    if not app:
        app = QCoreApplication([])
    
    # Create and start server
    server = NotificationServer(
        host="127.0.0.1",  # localhost for testing
        port=5005,
        logger=None
    )
    
    print("Starting notification server...")
    server.start()
    time.sleep(1.5)  # Give it time to start
    
    try:
        # Test GET request
        print("\n[TEST 1] Testing GET /")
        resp = requests.get("http://127.0.0.1:5005/", timeout=2)
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text}")
        
        # Test POST request
        print("\n[TEST 2] Testing POST with JSON")
        resp = requests.post(
            "http://127.0.0.1:5005/",
            json={"content": "Test notification"},
            timeout=2
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text}")
        
        # Test with query parameter
        print("\n[TEST 3] Testing GET with query param")
        resp = requests.get(
            "http://127.0.0.1:5005/?content=TestFromQuery",
            timeout=2
        )
        print(f"  Status: {resp.status_code}")
        print(f"  Response: {resp.text}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nStopping server...")
        server.stop()
        time.sleep(0.5)
        print("Server stopped")

if __name__ == "__main__":
    test_server()
