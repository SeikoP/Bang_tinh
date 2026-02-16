import os
import sys
import time

import requests

URL = "http://localhost:5005"


# ===== Auth =====
def get_auth_header():
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from core.config import Config

        key = Config.from_env().secret_key
        return {"Authorization": f"Bearer {key}"}
    except:
        return {}


def send_test(title, content):
    data = {
        "package": "com.vietinbank.ipay",
        "title": title,
        "content": content,
        "postTime": int(time.time() * 1000),
    }

    headers = get_auth_header()

    try:
        resp = requests.post(URL, json=data, headers=headers)
        print(f"Sent: {content[:50]}... | Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error sending: {e}")


# Case 1: Complex transfer with long message
msg1 = """Biến động số dư: Thời gian: 07/02/2026 03:30
Tài khoản: 107875070594
Giao dịch: +67,000VND
Số dư hiện tại: 1,545,606VND
Nội dung: CT DEN:422T2620B9D1SN8M MBVCB.12922428728.350539.DINH CONG LUONG chuyen tien.CT tu 9386565885 DINH CONG LUONG toi 107875070594 NGUYEN HUU CUONG tai VIETINBANK"""

# Case 2: Simple transfer
msg2 = """Biến động số dư: Thời gian: 07/02/2026 03:13
Tài khoản: 107875070594
Giao dịch: +20,000VND
Số dư hiện tại: 1,478,606VND
Nội dung: CT DEN:422T2620B8Q43T2H PHAN NGUYEN NAM ANH chuyen tien"""

# Case 3: Transfer with NAPAS
msg3 = """Biến động số dư: Thời gian: 07/02/2026 02:51
Tài khoản: 107875070594
Giao dịch: +20,000VND
Số dư hiện tại: 1,458,606VND
Nội dung: CT DEN:603719547897 NGUYEN XUAN TRUNG chuyen tien FT26038869732008; tai Napas"""

# Case 4: Small amounts (Even numbers)
amounts = ["10,000", "20,000", "30,000", "40,000", "50,000"]

print("--- Sending Real Cases ---")
send_test("VietinBank", msg1)
time.sleep(2)
send_test("VietinBank", msg2)
time.sleep(2)
send_test("VietinBank", msg3)
time.sleep(2)

print("\n--- Sending Small Amount Cases ---")
for amt in amounts:
    msg = f"""Biến động số dư: Thời gian: {time.strftime('%d/%m/%Y %H:%M')}
Tài khoản: 107875070594
Giao dịch: +{amt}VND
Số dư hiện tại: 1,550,000VND
Nội dung: CT DEN:123456 TEST USER chuyen tien"""
    send_test("VietinBank", msg)
    time.sleep(1.5)

print("\nDone!")
