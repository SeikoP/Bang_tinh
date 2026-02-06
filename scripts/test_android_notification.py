"""
Test Android notification forwarding
Gửi notification test và kiểm tra xem service có bắt được không
"""

import os
import subprocess
import sys
import time

ADB_PATH = os.path.join(
    os.environ.get("TEMP", "/tmp"), "adb", "platform-tools", "adb.exe"
)


def run_adb(args, timeout=5):
    """Run adb command"""
    try:
        result = subprocess.run(
            [ADB_PATH] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_device():
    """Check if device is connected"""
    success, stdout, _ = run_adb(["devices"])
    if not success:
        return False

    lines = stdout.strip().split("\n")
    devices = [l for l in lines[1:] if l.strip() and "device" in l]
    return len(devices) > 0


def clear_logcat():
    """Clear logcat"""
    run_adb(["logcat", "-c"])


def send_test_notification(package, title, content):
    """Send test notification via adb"""
    cmd = f'cmd notification post -S bigtext -t "{title}" "test_tag" "{content}"'

    # Nếu muốn fake package name, cần root
    # Với shell command, package sẽ là android hoặc com.android.shell
    success, stdout, stderr = run_adb(["shell", cmd])
    return success


def check_log_for_notification(timeout=3):
    """Check if notification was caught by service"""
    time.sleep(1)  # Đợi service xử lý

    success, stdout, _ = run_adb(
        ["logcat", "-d", "-s", "BankNotifier:D", "HttpSender:D"]
    )

    if not success:
        return False, "Cannot read logcat"

    # Tìm các dấu hiệu notification được xử lý
    indicators = [
        "Bank notification",
        "onNotificationPosted",
        "Attempting to send",
        "Notification received",
    ]

    for indicator in indicators:
        if indicator in stdout:
            return True, f"Found: {indicator}"

    return False, "No notification processing found in log"


def test_with_real_bank_package():
    """Test bằng cách cài app test có package name giống ngân hàng"""
    print("\n" + "=" * 60)
    print("🧪 Test 2: Check if service is listening")
    print("=" * 60)

    # Kiểm tra xem service có đang chạy không
    success, stdout, _ = run_adb(
        ["shell", "dumpsys", "activity", "services", "com.banknotifier"]
    )

    if "NotificationListenerService" in stdout:
        print("✅ Service is running")

        # Kiểm tra xem có bound không
        if "hasBound=true" in stdout:
            print("✅ Service is bound to system")
        else:
            print("❌ Service NOT bound to system")
            print("   → Need to toggle notification permission")
            return False
    else:
        print("❌ Service not found")
        return False

    return True


def test_notification_permission():
    """Test xem có quyền notification access không"""
    print("\n" + "=" * 60)
    print("🧪 Test 3: Check notification permission")
    print("=" * 60)

    success, stdout, _ = run_adb(["shell", "dumpsys", "notification"])

    if not success or not stdout:
        print("❌ Cannot check notification permission")
        return False

    if "com.banknotifier/com.banknotifier.NotificationListenerService" in stdout:
        print("✅ App has notification access permission")

        # Kiểm tra xem có trong enabled list không
        if "enabled for current profiles" in stdout:
            lines = stdout.split("\n")
            for i, line in enumerate(lines):
                if "enabled for current profiles" in line:
                    # Xem 10 dòng tiếp theo
                    next_lines = "\n".join(lines[i : i + 10])
                    if "com.banknotifier" in next_lines:
                        print("✅ Service is enabled")
                        return True

        print("⚠️  Permission granted but service may not be enabled")
        return False
    else:
        print("❌ App does NOT have notification access permission")
        print("   → Go to Settings and grant permission")
        return False


def main():
    print("=" * 60)
    print("🧪 Android Notification Forwarding Test")
    print("=" * 60)

    # Test 1: Device connection
    print("\n🧪 Test 1: Check device connection")
    if not check_device():
        print("❌ No device connected")
        print("   → Connect device via USB and enable USB debugging")
        return 1
    print("✅ Device connected")

    # Test 2: Service status
    if not test_with_real_bank_package():
        return 1

    # Test 3: Permission
    if not test_notification_permission():
        return 1

    # Test 4: Send test notification
    print("\n" + "=" * 60)
    print("🧪 Test 4: Send test notification")
    print("=" * 60)
    print("⚠️  Note: Shell notifications have package 'android' or 'com.android.shell'")
    print("   These will be FILTERED OUT by the app (only bank apps allowed)")
    print("   This test checks if onNotificationPosted() is called at all")

    clear_logcat()

    print("\n📤 Sending test notification...")
    if not send_test_notification("android", "Test Bank", "TK 123456 +1,000 VND"):
        print("❌ Failed to send notification")
        return 1

    print("✅ Notification sent")
    print("\n⏳ Checking log (3 seconds)...")

    caught, message = check_log_for_notification()

    if caught:
        print(f"✅ Service caught notification: {message}")
        print("\n🎉 SUCCESS! Service is working!")
        print("   Now it should work with real bank notifications")
    else:
        print(f"❌ Service did NOT catch notification: {message}")
        print("\n💡 Troubleshooting:")
        print("   1. Toggle notification permission (Settings → Apps → Bank Notifier)")
        print("   2. Force stop and restart the app")
        print("   3. Check if battery optimization is disabled")
        print("   4. Try rebooting the phone")

    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    print("To see real-time logs, run:")
    print("   python scripts/monitor_android_log.py")
    print("=" * 60)

    return 0 if caught else 1


if __name__ == "__main__":
    sys.exit(main())
