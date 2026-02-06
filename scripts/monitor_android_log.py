"""
Monitor Android logcat for Bank Notifier app
"""
import subprocess
import sys
import os
from datetime import datetime

ADB_PATH = os.path.join(os.environ.get('TEMP', '/tmp'), 'adb', 'platform-tools', 'adb.exe')

def check_adb():
    """Check if adb is available"""
    if not os.path.exists(ADB_PATH):
        print(f"❌ ADB not found at: {ADB_PATH}")
        print("Please run the setup first")
        return False
    return True

def check_device():
    """Check if device is connected"""
    try:
        result = subprocess.run([ADB_PATH, 'devices'], 
                              capture_output=True, text=True, timeout=5)
        lines = result.stdout.strip().split('\n')
        devices = [l for l in lines[1:] if l.strip() and 'device' in l]
        
        if not devices:
            print("❌ No Android device connected")
            print("Please connect device via USB and enable USB debugging")
            return False
        
        print(f"✅ Device connected: {devices[0].split()[0]}")
        return True
    except Exception as e:
        print(f"❌ Error checking device: {e}")
        return False

def monitor_log():
    """Monitor logcat for Bank Notifier"""
    print("=" * 60)
    print("📱 Monitoring Android Log for Bank Notifier")
    print("=" * 60)
    print("Tags: BankNotifier, HttpSender, NotificationListenerService")
    print("Press Ctrl+C to stop")
    print("-" * 60)
    
    try:
        # Clear old logs
        subprocess.run([ADB_PATH, 'logcat', '-c'], timeout=5)
        
        # Start monitoring
        process = subprocess.Popen(
            [ADB_PATH, 'logcat', '-s', 
             'BankNotifier:D', 'HttpSender:D', 'NotificationListenerService:D'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, b''):
            try:
                line = line.decode('utf-8', errors='ignore').strip()
            except:
                continue
            if line:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Color coding
                if 'Bank notification' in line:
                    print(f"[{timestamp}] 🏦 {line}")
                elif 'Error' in line or 'error' in line:
                    print(f"[{timestamp}] ❌ {line}")
                elif 'success' in line.lower():
                    print(f"[{timestamp}] ✅ {line}")
                else:
                    print(f"[{timestamp}] {line}")
                    
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopped monitoring")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if 'process' in locals():
            process.terminate()

def main():
    if not check_adb():
        return 1
    
    if not check_device():
        return 1
    
    monitor_log()
    return 0

if __name__ == '__main__':
    sys.exit(main())
