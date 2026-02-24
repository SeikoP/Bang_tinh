"""
Shared constants for the application.
Centralized bank package names and mappings to avoid duplication.
"""

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

# Test package names (for development/testing)
TEST_PACKAGES = {
    "com.test.bankapp",
    "com.example.notification",
    "android",  # For adb test notifications
}

# Combined set for notification filtering
ALL_BANK_PACKAGES = BANK_PACKAGES | TEST_PACKAGES

# ── App Info ──
APP_NAME = "WMS"
APP_VERSION = "2.0.0"
APP_AUTHOR = "WAREHOUSE"

# ── Export Settings ──
EXPORT_DATE_FORMAT = "%Y-%m-%d_%H%M%S"
PDF_PAGE_SIZE = "A4"

# ── Default Units ──
DEFAULT_UNITS = [
    {"name": "Thùng", "char": "t"},
    {"name": "Vỉ", "char": "v"},
    {"name": "Gói", "char": "g"},
    {"name": "Két", "char": "k"},
    {"name": "Hộp", "char": "h"},
    {"name": "Chai", "char": "c"},
]

# ── Pagination ──
ITEMS_PER_PAGE = 20
HISTORY_DAYS_DEFAULT = 30
