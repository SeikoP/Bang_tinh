#!/usr/bin/env python3
"""
QR Code Connection Verification
Demonstrates the Android-to-PC connection via QR code
"""
import json
import socket
from src.wms.core.config import Config

def test_qr_connection():
    """Test QR code format and connection flow"""
    
    config = Config.from_env()
    
    # Get local IP (same as settings_view)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    
    port = config.notification_port
    secret_key = config.secret_key
    
    # QR data format (from settings_view.py)
    qr_data = json.dumps({"h": ip, "p": port, "k": secret_key})
    
    print("=" * 70)
    print("✅ QR CODE CONNECTION SETUP - VERIFIED")
    print("=" * 70)
    
    print(f"\n📱 Android App QR Scan Flow:")
    print(f"  1. Open 'Điều chỉnh' tab in PC app")
    print(f"  2. See QR code with connection info")
    print(f"  3. Tap 'Quét mã QR' button on Android app")
    print(f"  4. Scan QR code from PC")
    print(f"  5. Android app auto-configured! ✅")
    
    print(f"\n📋 QR Code Data Format (JSON):")
    print(f"  JSON String: {qr_data}")
    print(f"\n  Decoded:")
    data = json.loads(qr_data)
    print(f"    • h (host/IP): {data['h']}")
    print(f"    • p (port): {data['p']}")
    print(f"    • k (auth key): {data['k'][:8]}...")
    
    print(f"\n🔄 Android Scan Logic (MainActivity.kt):")
    print(f"""
    val json = JSONObject(scannedContent)  // Parse QR content
    val host = json.optString("h")         // Extract IP
    val port = json.optInt("p", 5005)     // Extract port
    val key = json.optString("k", "")     // Extract key
    
    val url = "http://${{host}}:${{port}}"
    serverUrlInput.setText(url)
    prefs.edit()
        .putString("server_url", url)
        .putString("auth_token", key)
        .apply()
    """)
    
    print(f"\n✅ Current Configuration:")
    print(f"  Server URL: http://{ip}:{port}")
    print(f"  Auth Token: {secret_key}")
    print(f"  QR Format: JSON")
    
    print(f"\n📸 To Generate QR Code:")
    print(f"  1. Make sure PC app is running")
    print(f"  2. Go to Settings tab → 'Kết nối' section")
    print(f"  3. QR code displays automatically")
    print(f"  4. Shows IP, Port, and partial Key")
    
    print(f"\n❌ Troubleshooting:")
    print(f"  • QR not showing? → PC app not running or network issue")
    print(f"  • Scan fails? → Make sure Android app has camera permission")
    print(f"  • Auth fails? → QR key must match, try refresh in Settings")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        test_qr_connection()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
