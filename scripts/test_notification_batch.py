#!/usr/bin/env python
"""
Batch test for bank notifications

Sends multiple test notifications to verify the system.

Usage:
    python scripts/test_notification_batch.py
"""

import requests
import json
import sys
import time
from datetime import datetime


def send_notification(data, port=5005):
    """Send a single notification"""
    url = f"http://localhost:{port}"

    try:
        response = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}, timeout=5
        )
        return response.status_code == 200
    except:
        return False


def main():
    """Send multiple test notifications"""

    test_cases = [
        {
            "time": "08:30",
            "source": "VCB",
            "amount": "+500,000 VND",
            "content": "Chuyen tien tu NGUYEN VAN A",
        },
        {
            "time": "09:15",
            "source": "TCB",
            "amount": "+1,200,000 VND",
            "content": "Thanh toan don hang #12345",
        },
        {
            "time": "10:45",
            "source": "MB",
            "amount": "+750,000 VND",
            "content": "Nhan tien tu TRAN THI B",
        },
        {
            "time": "14:20",
            "source": "ACB",
            "amount": "+2,000,000 VND",
            "content": "Chuyen khoan nhanh",
        },
        {
            "time": "16:00",
            "source": "VCB",
            "amount": "+300,000 VND",
            "content": "Hoan tien",
        },
    ]

    print(f"Sending {len(test_cases)} test notifications...")
    print("=" * 60)

    success_count = 0

    for i, test_data in enumerate(test_cases, 1):
        print(
            f"\n[{i}/{len(test_cases)}] Sending: {test_data['source']} - {test_data['amount']}"
        )

        if send_notification(test_data):
            print("  ✓ Success")
            success_count += 1
        else:
            print("  ✗ Failed")

        # Small delay between requests
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print(f"Results: {success_count}/{len(test_cases)} successful")

    if success_count == len(test_cases):
        print("\n✓ All notifications sent successfully!")
        print("Check the 'Ngân hàng' tab in the application.")
        return 0
    else:
        print(f"\n✗ {len(test_cases) - success_count} notifications failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
