"""
Security Module - Authentication & Authorization
"""

import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Set


@dataclass
class DeviceCredentials:
    """Device authentication credentials"""

    device_id: str
    api_key: str
    device_name: str
    registered_at: float
    last_seen: float
    is_active: bool = True


class SecurityManager:
    """Manages authentication and authorization"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.devices: dict[str, DeviceCredentials] = {}
        self.rate_limiter = RateLimiter()
        self._load_devices()

    def _load_devices(self):
        """Load registered devices from config"""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                data = json.load(f)
                for device_data in data.get("devices", []):
                    device = DeviceCredentials(**device_data)
                    self.devices[device.device_id] = device

    def _save_devices(self):
        """Save devices to config"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "devices": [
                {
                    "device_id": d.device_id,
                    "api_key": d.api_key,
                    "device_name": d.device_name,
                    "registered_at": d.registered_at,
                    "last_seen": d.last_seen,
                    "is_active": d.is_active,
                }
                for d in self.devices.values()
            ]
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def generate_api_key(self) -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)

    def register_device(self, device_name: str) -> tuple[str, str]:
        """
        Register new device

        Returns:
            (device_id, api_key)
        """
        device_id = secrets.token_hex(16)
        api_key = self.generate_api_key()

        device = DeviceCredentials(
            device_id=device_id,
            api_key=api_key,
            device_name=device_name,
            registered_at=time.time(),
            last_seen=time.time(),
            is_active=True,
        )

        self.devices[device_id] = device
        self._save_devices()

        return device_id, api_key

    def authenticate(self, device_id: str, api_key: str, client_ip: str) -> bool:
        """
        Authenticate device

        Args:
            device_id: Device identifier
            api_key: API key
            client_ip: Client IP address

        Returns:
            True if authenticated
        """
        # Check rate limit
        if not self.rate_limiter.check(client_ip):
            return False

        # Check device exists
        device = self.devices.get(device_id)
        if not device:
            return False

        # Check device is active
        if not device.is_active:
            return False

        # Verify API key (constant-time comparison)
        if not hmac.compare_digest(device.api_key, api_key):
            return False

        # Update last seen
        device.last_seen = time.time()
        self._save_devices()

        return True

    def revoke_device(self, device_id: str):
        """Revoke device access"""
        if device_id in self.devices:
            self.devices[device_id].is_active = False
            self._save_devices()

    def list_devices(self) -> list[DeviceCredentials]:
        """List all registered devices"""
        return list(self.devices.values())


class RateLimiter:
    """Simple rate limiter"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    def check(self, client_id: str) -> bool:
        """
        Check if request is allowed

        Args:
            client_id: Client identifier (IP address)

        Returns:
            True if allowed
        """
        now = time.time()

        # Get request history
        if client_id not in self.requests:
            self.requests[client_id] = []

        # Remove old requests
        self.requests[client_id] = [
            req_time
            for req_time in self.requests[client_id]
            if now - req_time < self.window_seconds
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # Add new request
        self.requests[client_id].append(now)
        return True


class IPWhitelist:
    """IP address whitelist"""

    def __init__(self, allowed_ips: Optional[Set[str]] = None):
        self.allowed_ips = allowed_ips or set()
        # Always allow localhost
        self.allowed_ips.add("127.0.0.1")
        self.allowed_ips.add("::1")

    def is_allowed(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        # If no whitelist, allow all
        if not self.allowed_ips:
            return True
        return ip in self.allowed_ips

    def add(self, ip: str):
        """Add IP to whitelist"""
        self.allowed_ips.add(ip)

    def remove(self, ip: str):
        """Remove IP from whitelist"""
        self.allowed_ips.discard(ip)


class InputValidator:
    """Input validation"""

    @staticmethod
    def validate_notification_content(content: str) -> bool:
        """Validate notification content"""
        if not content:
            return False

        # Max length
        if len(content) > 10000:
            return False

        # Must be valid UTF-8
        try:
            content.encode("utf-8")
        except UnicodeEncodeError:
            return False

        return True

    @staticmethod
    def validate_device_name(name: str) -> bool:
        """Validate device name"""
        if not name or len(name) > 100:
            return False

        # Only alphanumeric, spaces, dashes
        import re

        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", name):
            return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        import re

        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")
        # Remove parent directory references
        filename = filename.replace("..", "_")
        # Remove special characters
        filename = re.sub(r"[^\w\s\-.]", "_", filename)
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        return filename
