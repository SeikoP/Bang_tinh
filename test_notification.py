import requests
import time

def test_rich_notifications():
    url = "http://127.0.0.1:5005"
    
    # Bo cac ky tu unicode dac biet de tranh loi console Windows khi print
    test_cases = [
        "MOMO: Ban da nhan duoc +150,000d tu TRAN VAN B. Loi nhan: thanh toan don hang #123",
        "Vietcombank: TK 0011xxx +5,000,000 VND luc 23:45. SD: 12,000,000 VND. ND: Luong thang 02",
        "MB Bank: TK 99999xxx +20,000d; tai 23:46; ND: thue xe thang 2",
        "TPBank: +10,500 vao TK 1234xxx. ND: Chuyen tien noi bo",
        "Thong bao khac: Co tin nhan moi tu khach hang quan tam san pham."
    ]
    
    print("--- Start sending test notifications ---")
    
    for msg in test_cases:
        try:
            params = {"content": msg}
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                print(f" -> Sent: {msg[:40]}...")
            else:
                print(f" -> Server Error: {response.status_code}")
        except Exception as e:
            print(f" -> Connection Error: {e}")
            break
            
        time.sleep(3)

    print("\n--- Test finished ---")

if __name__ == "__main__":
    test_rich_notifications()
