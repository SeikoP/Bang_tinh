"""
Shared constants for the application.
Centralized bank package names, UI defaults, and domain-specific settings.
"""

import os

# === App Info ===
APP_NAME = os.getenv("APP_NAME", "WMS")
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
APP_AUTHOR = "WAREHOUSE"

# === Window Settings ===
WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))
WINDOW_MIN_WIDTH = 850
WINDOW_MIN_HEIGHT = 600

# === Export Settings ===
EXPORT_DATE_FORMAT = "%Y-%m-%d_%H%M%S"
PDF_PAGE_SIZE = "A4"
ITEMS_PER_PAGE = 20
HISTORY_DAYS_DEFAULT = 30

# === Default Units (Vietnamese) ===
DEFAULT_UNITS = [
    {"name": "Thùng", "char": "t"},
    {"name": "Vỉ", "char": "v"},
    {"name": "Gói", "char": "g"},
    {"name": "Két", "char": "k"},
    {"name": "Hộp", "char": "h"},
    {"name": "Chai", "char": "c"},
]

# Package name -> Display name mapping for Vietnamese banks
BANK_PACKAGE_MAP = {
    "com.mservice.momotransfer": "MoMo",
    "com.vnpay.wallet": "VNPay",
    "com.vietcombank.mobile": "Vietcombank",
    "com.vietinbank.ipay": "VietinBank",
    "com.techcombank.bb.app": "Techcombank",
    "com.mbmobile": "MB Bank",
    "com.vnpay.bidv": "BIDV",
    "com.acb.acbmobile": "ACB",
    "com.tpb.mb.gprsandroid": "TPBank",
    "com.msb.mbanking": "MSB",
    "com.agribank.mobilebanking": "Agribank",
    "com.sacombank.mbanking": "Sacombank",
    "com.hdbank.mobilebanking": "HDBank",
    "com.vpbank.mobilebanking": "VPBank",
    "com.ocb.mobilebanking": "OCB",
    "com.shb.mobilebanking": "SHB",
    "com.scb.mobilebanking": "SCB",
    "com.seabank.mobilebanking": "SeaBank",
    "com.vib.mobilebanking": "VIB",
    "com.lienvietpostbank.mobilebanking": "LienVietPostBank",
    "com.bvbank.mobilebanking": "BaoVietBank",
    "com.pvcombank.mobilebanking": "PVcomBank",
}

# Set of all bank package names (for fast lookup/filtering)
BANK_PACKAGES = set(BANK_PACKAGE_MAP.keys())

# SMS / Messaging apps — bank transaction alerts often arrive as SMS,
# not from the bank app itself.  Adding these ensures SMS-based alerts
# are forwarded to the PC (content filtering happens in bank_parser).
SMS_PACKAGES = {
    "com.android.mms",                      # AOSP / Generic Android
    "com.android.messaging",               # AOSP Messaging (many OEMs)
    "com.google.android.apps.messaging",   # Google Messages
    "com.samsung.android.messaging",       # Samsung Messages
    "com.miui.messaging",                  # Xiaomi MIUI
    "com.miui.sms",                        # Xiaomi (older MIUI)
    "com.vivo.messaging",                  # Vivo
    "com.oppo.mms",                        # OPPO
    "com.coloros.mms",                     # ColorOS (OPPO/Realme)
    "com.realme.messaging",                # Realme
    "com.asus.message",                    # Asus
}

# Extra fintech / e-wallet packages not covered in BANK_PACKAGE_MAP
FINTECH_PACKAGES = {
    "vn.com.vng.zalopay",                  # ZaloPay
    "com.shopee.vn",                       # ShopeePay (Vietnam)
    "com.teko.grabpay.vn",                 # GrabPay Vietnam
    "com.grab.passenger",                  # Grab (general)
    "com.foxpay.app",                      # FoxPay
    "vn.payoo.customer",                   # Payoo
    "com.viettel.money",                   # Viettel Money
    "com.viettelpay",                      # Viettel Pay
    "com.momo.vnpt",                       # VNPT Money
}

# Test package names (for development/testing)
TEST_PACKAGES = {
    "com.test.bankapp",
    "com.example.notification",
    "com.banknotifier",  # Self-test notifications from Bank Notifier app
    "android",  # For adb test notifications
}

# Combined set for notification filtering
ALL_BANK_PACKAGES = BANK_PACKAGES | SMS_PACKAGES | FINTECH_PACKAGES | TEST_PACKAGES

