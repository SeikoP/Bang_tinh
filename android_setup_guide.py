#!/usr/bin/env python3
"""
Android Notification Server - Setup Guide & Test Tool
Hướng dẫn kết nối Android app tới PC
"""
import socket
import sys
import json
from src.wms.core.config import Config

def get_local_ip():
    """Get local IP address (not 127.0.0.1, not 0.0.0.0)"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a public DNS to find local IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def main():
    config = Config.from_env()
    
    print("=" * 70)
    print("🔌 ANDROID NOTIFICATION SERVER CONNECTION SETUP")
    print("=" * 70)
    
    # Get local IP
    local_ip = get_local_ip()
    port = config.notification_port
    secret_key = config.secret_key
    
    print(f"\n📱 Android App Configuration:")
    print(f"  Server URL: http://{local_ip}:{port}")
    print(f"  Authorization Token: {secret_key}")
    
    print(f"\n🔒 Authentication:")
    print(f"  Add header to requests:")
    print(f"    Authorization: Bearer {secret_key}")
    print(f"\n  Example (curl):")
    print(f'    curl -H "Authorization: Bearer {secret_key}" \\')
    print(f"         http://{local_ip}:{port}/?content=test")
    
    print(f"\n📋 Request Format (JSON):")
    print(f"""
    POST http://{local_ip}:{port}/
    Content-Type: application/json
    Authorization: Bearer {secret_key}
    
    {{
      "content": "Your notification message",
      "package": "com.bank.app",
      "title": "Bank Name"
    }}
    """)
    
    print(f"\n🧪 Test Steps:")
    print(f"  1. On Android/Smartphone:")
    print(f"     - Connect to same WiFi as PC")
    print(f"     - Send POST request to: http://{local_ip}:{port}/")
    print(f"     - Include Bearer token in Authorization header")
    print(f"\n  2. Make sure PC app is running (check for 'Notification Server started' log)")
    print(f"\n  3. Firewall might block port {port}:")
    print(f"     - Check Windows Defender Firewall")
    print(f"     - Add rule: Allow TCP port {port} inbound")
    
    print(f"\n❌ Common Issues:")
    print(f"  • 401 Unauthorized → Missing/wrong Bearer token")
    print(f"  • Connection refused → Server not running or firewall blocking")
    print(f"  • Timeout → Check WiFi connection or firewall blocking port")
    print(f"  • \"Cannot reach server\" → Wrong IP or not on same network")
    
    print(f"\n✅ Config Summary:")
    print(json.dumps({
        "server_url": f"http://{local_ip}:{port}",
        "auth_token": secret_key,
        "port": port,
        "local_ip": local_ip,
        "same_network_required": True,
        "firewall_note": f"Allow inbound TCP:{port}"
    }, indent=2))
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
