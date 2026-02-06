#!/usr/bin/env python
"""
Universal notification test script for both local and build environments

Tests notification system by sending test bank notifications.
Automatically detects if running against local dev or built executable.

Usage:
    # Test local development
    python scripts/test_notification_universal.py

    # Test built executable
    python scripts/test_notification_universal.py --build

    # Send multiple notifications
    python scripts/test_notification_universal.py --batch

    # Custom host/port
    python scripts/test_notification_universal.py --host 192.168.1.100 --port 5005
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import requests


class NotificationTester:
    """Test notification system"""

    def __init__(self, host="localhost", port=5005, verbose=True):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.url = f"http://{host}:{port}"

    def send_notification(self, data):
        """Send a single notification"""
        try:
            response = requests.post(
                self.url,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            return response.status_code == 200, response
        except requests.exceptions.ConnectionError:
            return False, "Connection refused"
        except Exception as e:
            return False, str(e)

    def test_single(self):
        """Send a single test notification"""
        test_data = {
            "time": datetime.now().strftime("%H:%M"),
            "source": "VCB",
            "amount": "+1,000,000 VND",
            "content": "Test notification - Single",
        }

        if self.verbose:
            print(f"🔔 Sending test notification to {self.url}")
            print(f"📦 Data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
            print()

        success, response = self.send_notification(test_data)

        if success:
            if self.verbose:
                print("✅ Notification sent successfully!")
                print(f"📊 Response: {response.status_code}")
                print("👉 Check the 'Ngân hàng' tab in the application")
            return True
        else:
            if self.verbose:
                print("❌ Failed to send notification")
                print(f"⚠️  Error: {response}")
            return False

    def test_batch(self, count=5):
        """Send multiple test notifications"""
        test_cases = [
            {
                "time": "08:30",
                "source": "VCB",
                "amount": "+500,000 VND",
                "content": "Chuyển tiền từ NGUYEN VAN A",
            },
            {
                "time": "09:15",
                "source": "TCB",
                "amount": "+1,200,000 VND",
                "content": "Thanh toán đơn hàng #12345",
            },
            {
                "time": "10:45",
                "source": "MB",
                "amount": "+750,000 VND",
                "content": "Nhận tiền từ TRAN THI B",
            },
            {
                "time": "14:20",
                "source": "ACB",
                "amount": "+2,000,000 VND",
                "content": "Chuyển khoản nhanh",
            },
            {
                "time": "16:00",
                "source": "VCB",
                "amount": "+300,000 VND",
                "content": "Hoàn tiền",
            },
        ]

        # Limit to requested count
        test_cases = test_cases[:count]

        if self.verbose:
            print(f"🔔 Sending {len(test_cases)} test notifications to {self.url}")
            print("=" * 70)

        success_count = 0

        for i, test_data in enumerate(test_cases, 1):
            if self.verbose:
                print(
                    f"\n[{i}/{len(test_cases)}] {test_data['source']} - {test_data['amount']}"
                )

            success, _ = self.send_notification(test_data)

            if success:
                if self.verbose:
                    print("  ✅ Success")
                success_count += 1
            else:
                if self.verbose:
                    print("  ❌ Failed")

            # Small delay between requests
            time.sleep(0.3)

        if self.verbose:
            print("\n" + "=" * 70)
            print(f"📊 Results: {success_count}/{len(test_cases)} successful")

            if success_count == len(test_cases):
                print("\n✅ All notifications sent successfully!")
                print("👉 Check the 'Ngân hàng' tab in the application")
            else:
                print(f"\n⚠️  {len(test_cases) - success_count} notifications failed")

        return success_count == len(test_cases)

    def check_connection(self):
        """Check if notification server is reachable"""
        try:
            response = requests.get(self.url, timeout=2)
            return True
        except:
            return False


def detect_environment():
    """Detect if running against local or build"""
    # Check if dist folder exists (indicates build environment)
    dist_path = Path("dist")
    if dist_path.exists() and any(dist_path.glob("*.exe")):
        return "build"
    return "local"


def main():
    parser = argparse.ArgumentParser(
        description="Universal notification test for local and build environments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test local development
  python scripts/test_notification_universal.py
  
  # Test built executable
  python scripts/test_notification_universal.py --build
  
  # Send 10 test notifications
  python scripts/test_notification_universal.py --batch --count 10
  
  # Test remote server
  python scripts/test_notification_universal.py --host 192.168.1.100
        """,
    )

    parser.add_argument(
        "--host",
        default="localhost",
        help="Notification server host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5005,
        help="Notification server port (default: 5005)",
    )
    parser.add_argument(
        "--batch", action="store_true", help="Send multiple test notifications"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of notifications in batch mode (default: 5)",
    )
    parser.add_argument(
        "--build", action="store_true", help="Indicate testing against built executable"
    )
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    args = parser.parse_args()

    # Detect environment
    env = "build" if args.build else detect_environment()

    if not args.quiet:
        print("=" * 70)
        print("🧪 Notification System Test")
        print("=" * 70)
        print(f"🎯 Environment: {env.upper()}")
        print(f"🌐 Target: {args.host}:{args.port}")
        print(f"📋 Mode: {'Batch' if args.batch else 'Single'}")
        print("=" * 70)
        print()

    # Create tester
    tester = NotificationTester(host=args.host, port=args.port, verbose=not args.quiet)

    # Check connection first
    if not args.quiet:
        print("🔍 Checking connection...")

    if not tester.check_connection():
        print("❌ Cannot connect to notification server!")
        print(f"⚠️  Make sure the application is running on {args.host}:{args.port}")
        return 1

    if not args.quiet:
        print("✅ Connection OK")
        print()

    # Run test
    if args.batch:
        success = tester.test_batch(count=args.count)
    else:
        success = tester.test_single()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
