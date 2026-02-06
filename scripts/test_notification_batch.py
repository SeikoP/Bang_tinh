"""
Test script to send multiple bank notifications with various formats
"""

import json
import time

import requests

# Test data: 30 different notifications from various banks
TEST_NOTIFICATIONS = [
    # VietinBank
    {
        "content": "Biến động số dư: CT DI:603709817078 NGUYEN VAN A Chuyen tien 500.000 VND",
        "package": "com.vietinbank.ipay",
    },
    {
        "content": "Biến động số dư: CT DI:603709817079 TRAN THI B Chuyen tien 1.200.000 VND",
        "package": "com.vietinbank.ipay",
    },
    {
        "content": "Biến động số dư: CT DI:603709817080 LE VAN C Chuyen tien 750.000 VND",
        "package": "com.vietinbank.ipay",
    },
    {
        "content": "Biến động số dư: CT DI:603709817081 PHAM THI D Chuyen tien 2.500.000 VND",
        "package": "com.vietinbank.ipay",
    },
    {
        "content": "Biến động số dú: CT DI:603709817082 HOANG VAN E Chuyen tien 350.000 VND",
        "package": "com.vietinbank.ipay",
    },
    # MoMo
    {
        "content": "Nhận tiền chuyển khoản từ NGUYEN MINH F: Số tiền 100.000 ₫",
        "package": "com.mservice.momotransfer",
    },
    {
        "content": "Nhận tiền chuyển khoản từ TRAN VAN G: Số tiền 250.000 ₫",
        "package": "com.mservice.momotransfer",
    },
    {
        "content": "Nhận tiền chuyển khoản từ LE THI H: Số tiền 500.000 ₫",
        "package": "com.mservice.momotransfer",
    },
    {
        "content": "Nhận tiền chuyển khoản từ PHAM VAN I: Số tiền 1.000.000 ₫",
        "package": "com.mservice.momotransfer",
    },
    {
        "content": "Nhận tiền chuyển khoản từ HOANG THI K: Số tiền 150.000 ₫",
        "package": "com.mservice.momotransfer",
    },
    # Vietcombank
    {
        "content": "Chuyen tien tu NGUYEN VAN L 800.000 VND Ref:VCB123456",
        "package": "com.vietcombank.mobile",
    },
    {
        "content": "Chuyen tien tu TRAN THI M 1.500.000 VND Ref:VCB123457",
        "package": "com.vietcombank.mobile",
    },
    {
        "content": "Chuyen tien tu LE VAN N 600.000 VND Ref:VCB123458",
        "package": "com.vietcombank.mobile",
    },
    {
        "content": "Chuyen tien tu PHAM THI O 2.000.000 VND Ref:VCB123459",
        "package": "com.vietcombank.mobile",
    },
    {
        "content": "Chuyen tien tu HOANG VAN P 450.000 VND Ref:VCB123460",
        "package": "com.vietcombank.mobile",
    },
    # Techcombank
    {
        "content": "ND Chuyen tien tu NGUYEN MINH Q. So tien: 900.000 VND",
        "package": "com.techcombank.bb.app",
    },
    {
        "content": "ND Chuyen tien tu TRAN VAN R. So tien: 1.800.000 VND",
        "package": "com.techcombank.bb.app",
    },
    {
        "content": "ND Chuyen tien tu LE THI S. So tien: 650.000 VND",
        "package": "com.techcombank.bb.app",
    },
    {
        "content": "ND Chuyen tien tu PHAM VAN T. So tien: 3.000.000 VND",
        "package": "com.techcombank.bb.app",
    },
    {
        "content": "ND Chuyen tien tu HOANG THI U. So tien: 400.000 VND",
        "package": "com.techcombank.bb.app",
    },
    # MB Bank
    {
        "content": "ND: NGUYEN VAN V chuyen tien 700.000 VND MBVCB.123456",
        "package": "com.mbmobile",
    },
    {
        "content": "ND: TRAN THI W chuyen tien 1.600.000 VND MBVCB.123457",
        "package": "com.mbmobile",
    },
    {
        "content": "ND: LE VAN X chuyen tien 550.000 VND MBVCB.123458",
        "package": "com.mbmobile",
    },
    {
        "content": "ND: PHAM THI Y chuyen tien 2.200.000 VND MBVCB.123459",
        "package": "com.mbmobile",
    },
    {
        "content": "ND: HOANG VAN Z chuyen tien 380.000 VND MBVCB.123460",
        "package": "com.mbmobile",
    },
    # ACB
    {
        "content": "Nhan tien tu NGUYEN HOANG AA 850.000 VND FT24037123456",
        "package": "com.acb.acbmobile",
    },
    {
        "content": "Nhan tien tu TRAN VAN BB 1.700.000 VND FT24037123457",
        "package": "com.acb.acbmobile",
    },
    {
        "content": "Nhan tien tu LE THI CC 620.000 VND FT24037123458",
        "package": "com.acb.acbmobile",
    },
    {
        "content": "Nhan tien tu PHAM VAN DD 2.800.000 VND FT24037123459",
        "package": "com.acb.acbmobile",
    },
    {
        "content": "Nhan tien tu HOANG THI EE 420.000 VND FT24037123460",
        "package": "com.acb.acbmobile",
    },
]


def send_notification(url, data, delay=0.5):
    """Send a single notification"""
    try:
        response = requests.get(url, params={"content": json.dumps(data)}, timeout=5)
        if response.status_code == 200:
            print(f"✅ Sent: {data['package'][:20]}... - {data['content'][:50]}...")
            return True
        else:
            print(f"❌ Failed ({response.status_code}): {data['content'][:50]}...")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        time.sleep(delay)


def main():
    url = "http://192.168.2.17:5005"

    print("=" * 80)
    print("📱 Bank Notification Batch Test")
    print("=" * 80)
    print(f"Target: {url}")
    print(f"Total notifications: {len(TEST_NOTIFICATIONS)}")
    print("=" * 80)
    print()

    success_count = 0
    failed_count = 0

    for i, notif in enumerate(TEST_NOTIFICATIONS, 1):
        print(f"[{i}/{len(TEST_NOTIFICATIONS)}] ", end="")
        if send_notification(url, notif):
            success_count += 1
        else:
            failed_count += 1

    print()
    print("=" * 80)
    print("📊 Test Results")
    print("=" * 80)
    print(f"✅ Success: {success_count}/{len(TEST_NOTIFICATIONS)}")
    print(f"❌ Failed: {failed_count}/{len(TEST_NOTIFICATIONS)}")
    print(f"📈 Success rate: {success_count/len(TEST_NOTIFICATIONS)*100:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
