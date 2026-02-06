#!/usr/bin/env python
"""
Test sender name extraction with real bank notification messages
"""

import re

def extract_sender_name(text):
    """Extract sender name from bank notification message"""
    patterns = [
        # Format: "ND Chuyen tien tu TEN" or "ND Nhan tien tu TEN"
        r"ND\s+Chuyen\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
        r"ND\s+Nhan\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
        # Format: "Chuyen tien tu TEN" or "Nhan tien tu TEN" (without ND prefix)
        r"Chuyen\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
        r"Nhan\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
        # Format: "ND: TEN chuyen tien" or "ND: TEN nhan tien" (name comes first, then action)
        r"ND[:\s]+([A-Z][A-Z\s]+?)(?:\s+chuyen|\s+nhan|\s+Ref|\s+MBVCB|\s+FT\d+|\s*\.|,|$)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up: remove trailing reference codes only
            name = re.sub(r'\s*(Ref|MBVCB|FT\d+).*$', '', name, flags=re.IGNORECASE)
            # Remove trailing action words only if they appear at the end
            name = re.sub(r'\s+(chuyen\s+tien|nhan\s+tien|chuyen\s+khoan|nhan\s+khoan)$', '', name, flags=re.IGNORECASE)
            # Remove trailing punctuation and whitespace
            name = re.sub(r'[,.\s]+$', '', name)
            name = name.strip()
            # Valid name should be at least 3 chars
            if len(name) >= 3:
                return name[:50]
    
    return ""

# Test cases with real Vietnamese bank notification formats
test_cases = [
    # Vietinbank format
    ("TK 1234567890 GD +3,000,000 VND luc 20:15 05/02. SD 18,000,000 VND. ND Chuyen tien tu NGUYEN VAN A", "NGUYEN VAN A"),
    ("TK 9876543210 +2,500,000 VND vao 14:30. ND Nhan tien tu TRAN THI B. Ref VTB.123456", "TRAN THI B"),
    ("Vietinbank: TK 1111222233 +1,500,000 VND vao 10:00. ND Chuyen tien tu LE VAN C", "LE VAN C"),
    ("VTB: TK 4444555566 +800,000 VND. ND Nhan tien tu PHAM THI D. Ref VTB.789012", "PHAM THI D"),
    ("VTB: +5,000,000d. ND: NGUYEN MINH TUAN chuyen tien", "NGUYEN MINH TUAN"),
    
    # Techcombank format
    ("TCB: +1,200,000 VND. ND Chuyen tien tu HOANG VAN E", "HOANG VAN E"),
    ("Techcombank TK 7777888899 +3,500,000 VND. ND Nhan tien tu NGUYEN THI F. Ref TCB.345678", "NGUYEN THI F"),
    ("Techcombank: +2,300,000d. ND: Chuyen tien tu TRAN VAN HUNG", "TRAN VAN HUNG"),
    ("TCB: TK 123456789 +1,800,000 VND. ND: LE THI MAI chuyen khoan", "LE THI MAI"),
    
    # MBBank format
    ("MB: TK 1234567890 +2,000,000 VND. ND Chuyen tien tu DO VAN G", "DO VAN G"),
    ("MBBank +1,800,000 VND vao 16:45. ND Nhan tien tu BUI THI H. Ref MBVCB.901234", "BUI THI H"),
    ("MB: +3,200,000d. ND Nhan tien tu PHAM VAN LONG. MBVCB.123456", "PHAM VAN LONG"),
    ("MBBank: TK 987654321 +1,500,000 VND. ND: HOANG THI LAN chuyen tien", "HOANG THI LAN"),
    
    # ACB format
    ("ACB: +2,200,000 VND. ND Chuyen tien tu DANG VAN I", "DANG VAN I"),
    ("ACB TK 9999000011 +1,600,000 VND. ND Nhan tien tu VO THI K. Ref ACB.567890", "VO THI K"),
    ("ACB: +4,500,000d. ND: Chuyen tien tu NGUYEN THANH NAM", "NGUYEN THANH NAM"),
    ("ACB TK 111222333 +2,800,000 VND. ND: TRAN THI HUONG nhan tien", "TRAN THI HUONG"),
    
    # TPBank format
    ("TPBank: +900,000 VND. ND Chuyen tien tu TRUONG VAN L", "TRUONG VAN L"),
    ("TP: TK 2222333344 +1,100,000 VND. ND Nhan tien tu PHAN THI M. Ref TP.123456", "PHAN THI M"),
    ("TPBank: +3,700,000d. ND: LE VAN QUANG chuyen tien", "LE VAN QUANG"),
    
    # VPBank format
    ("VPBank: +2,600,000 VND. ND Chuyen tien tu NGUYEN THI THAO", "NGUYEN THI THAO"),
    ("VPB: TK 444555666 +1,900,000d. ND: Nhan tien tu PHAM VAN TUAN", "PHAM VAN TUAN"),
    
    # Sacombank format
    ("Sacombank: +3,100,000 VND. ND Chuyen tien tu TRAN VAN MINH", "TRAN VAN MINH"),
    ("STB: TK 777888999 +2,400,000d. ND: LE THI HONG nhan tien", "LE THI HONG"),
    
    # BIDV format
    ("BIDV: +4,200,000 VND. ND Chuyen tien tu NGUYEN VAN KIEN", "NGUYEN VAN KIEN"),
    ("BIDV TK 123123123 +1,700,000d. ND: Nhan tien tu HOANG THI LINH", "HOANG THI LINH"),
    
    # Agribank format
    ("Agribank: +2,900,000 VND. ND Chuyen tien tu PHAM VAN DAT", "PHAM VAN DAT"),
    ("AGB: TK 456456456 +3,300,000d. ND: VO THI NGOC nhan tien", "VO THI NGOC"),
    
    # Short names (2 words)
    ("TK 1234567890 +500,000 VND. ND Chuyen tien tu MINH ANH", "MINH ANH"),
    ("TK 9876543210 +750,000 VND. ND Nhan tien tu THANH TUNG", "THANH TUNG"),
    
    # Long names (4 words)
    ("TK 1111222233 +1,300,000 VND. ND Chuyen tien tu NGUYEN HOANG MINH ANH", "NGUYEN HOANG MINH ANH"),
    ("TK 4444555566 +1,700,000 VND. ND Nhan tien tu TRAN THI THANH THUY", "TRAN THI THANH THUY"),
    
    # With Ref/MBVCB/FT at the end
    ("TK 7777888899 +2,100,000 VND. ND Chuyen tien tu LE VAN NAM. Ref MBVCB.123456", "LE VAN NAM"),
    ("TK 1234567890 +1,400,000 VND. ND Nhan tien tu PHAM THI LAN. Ref FT12345678", "PHAM THI LAN"),
    ("TK 9999888877 +3,600,000 VND. ND: NGUYEN VAN HAI. MBVCB.789012", "NGUYEN VAN HAI"),
    
    # Mixed case and punctuation
    ("TK 5555666677 +2,700,000 VND. ND: Chuyen tien tu TRAN THI MY.", "TRAN THI MY"),
    ("TK 8888999900 +1,200,000 VND. ND Nhan tien tu LE VAN TUAN,", "LE VAN TUAN"),
    
    # Without "tu" keyword
    ("TK 3333444455 +4,100,000 VND. ND: PHAM THI HUYEN chuyen khoan", "PHAM THI HUYEN"),
    ("TK 6666777788 +2,500,000 VND. ND HOANG VAN LONG nhan tien", "HOANG VAN LONG"),
    
    # Edge cases - too short (should return empty)
    ("TK 9999000011 +600,000 VND. ND Chuyen tien tu A", ""),
    ("TK 2222333344 +850,000 VND. ND Nhan tien tu AB", ""),
    ("TK 1111000022 +950,000 VND. ND: XY", ""),
]

print("=" * 80)
print("Testing Sender Name Extraction")
print("=" * 80)

passed = 0
failed = 0

for i, (message, expected) in enumerate(test_cases, 1):
    result = extract_sender_name(message)
    status = "✓ PASS" if result == expected else "✗ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"\n[{i:2d}] {status}")
    print(f"  Message: {message[:70]}...")
    print(f"  Expected: '{expected}'")
    print(f"  Got:      '{result}'")

print("\n" + "=" * 80)
print(f"Results: {passed}/{len(test_cases)} passed, {failed}/{len(test_cases)} failed")
print("=" * 80)

if failed == 0:
    print("\n✓ All tests passed!")
    exit(0)
else:
    print(f"\n✗ {failed} test(s) failed")
    exit(1)
