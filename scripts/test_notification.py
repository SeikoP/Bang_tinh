#!/usr/bin/env python
"""
Test script for bank notification

Sends a test notification to the running application.

Usage:
    python scripts/test_notification.py
"""

import json
import sys
from datetime import datetime

import requests


def send_test_notification(port=5005, host="localhost"):
    """Send a test bank notification"""

    url = f"http://{host}:{port}"

    # Test notification data
    test_data = {
        "time": datetime.now().strftime("%H:%M"),
        "source": "VCB",
        "amount": "+1,000,000 VND",
        "content": "Test notification from test script",
    }

    print(f"Sending test notification to {url}...")
    print(f"Data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")

    try:
        response = requests.post(
            url, json=test_data, headers={"Content-Type": "application/json"}, timeout=5
        )

        print(f"\nResponse status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            print("\n✓ Test notification sent successfully!")
            print("Check the 'Ngân hàng' tab in the application.")
            return 0
        else:
            print(f"\n✗ Failed to send notification: {response.status_code}")
            return 1

    except requests.exceptions.ConnectionError:
        print("\n✗ Connection failed!")
        print("Make sure the application is running.")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Send test bank notification to the application"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5005,
        help="Notification server port (default: 5005)",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Notification server host (default: localhost)",
    )

    args = parser.parse_args()

    return send_test_notification(port=args.port, host=args.host)


if __name__ == "__main__":
    sys.exit(main())
