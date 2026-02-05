"""License key validation system with RSA signature verification"""

import base64
import json
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.exceptions import InvalidSignature

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from core.exceptions import ValidationError


class LicenseValidator:
    """
    Validates application license keys using RSA signature verification.

    License key format: <base64_payload>.<base64_signature>

    Payload structure (JSON):
    {
        "customer": "Customer Name",
        "email": "customer@example.com",
        "issued": "2025-01-01T00:00:00",
        "expiry": "2026-01-01T00:00:00",
        "features": ["feature1", "feature2"],
        "max_users": 10
    }
    """

    # Default public key for demo/testing (replace with real key in production)
    DEFAULT_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy8Dbv8prpJ/0kKhlGeJY
ozo2t60EG8EocOo8h1BXIHvMUfGe7oVjK1o9atUeh03o/atTx/7gE0K3o8b6fL9E
6FBXoqDhiVDI+ky6s0rnJXpNwty0NNKJtmIYsqONpzKJ7WTktrqnOfKf1/+WK8DX
v3xKCQKCAQEAy8Dbv8prpJ/0kKhlGeJYozo2t60EG8EocOo8h1BXIHvMUfGe7oVj
K1o9atUeh03o/atTx/7gE0K3o8b6fL9E6FBXoqDhiVDI+ky6s0rnJXpNwty0NNKJ
tmIYsqONpzKJ7WTktrqnOfKf1/+WK8DXv3xKCQIDAQAB
-----END PUBLIC KEY-----"""

    def __init__(
        self,
        public_key_pem: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize license validator.

        Args:
            public_key_pem: PEM-encoded RSA public key (uses default if None)
            logger: Logger instance

        Raises:
            ValidationError: If cryptography library not available
        """
        if not CRYPTO_AVAILABLE:
            raise ValidationError(
                "Cryptography library not installed. Install with: pip install cryptography",
                "crypto_library",
            )

        self.logger = logger or logging.getLogger(__name__)

        # Load public key
        pem_data = public_key_pem or self.DEFAULT_PUBLIC_KEY_PEM
        try:
            self.public_key = serialization.load_pem_public_key(
                pem_data.encode("utf-8")
            )
            self.logger.info("License validator initialized with public key")
        except Exception as e:
            self.logger.error(f"Failed to load public key: {e}")
            raise ValidationError("Invalid public key format", "public_key") from e

    def validate(self, license_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate license key and return license data.

        Args:
            license_key: License key string in format <payload>.<signature>

        Returns:
            Tuple of (is_valid, license_data)
            - is_valid: True if license is valid, False otherwise
            - license_data: Dictionary with license information (empty if invalid)
        """
        try:
            # Parse license key
            parts = license_key.strip().split(".")
            if len(parts) != 2:
                self.logger.warning("Invalid license key format: missing signature")
                return False, {}

            payload_b64, signature_b64 = parts

            # Decode payload and signature
            try:
                payload = base64.b64decode(payload_b64)
                signature = base64.b64decode(signature_b64)
            except Exception as e:
                self.logger.warning(f"Failed to decode license key: {e}")
                return False, {}

            # Verify signature
            try:
                self.public_key.verify(
                    signature,
                    payload,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
            except InvalidSignature:
                self.logger.warning("License key signature verification failed")
                return False, {}

            # Parse license data
            try:
                license_data = json.loads(payload.decode("utf-8"))
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse license data: {e}")
                return False, {}

            # Validate required fields
            required_fields = ["customer", "issued", "expiry"]
            for field in required_fields:
                if field not in license_data:
                    self.logger.warning(f"License missing required field: {field}")
                    return False, {}

            # Check expiration
            try:
                expiry = datetime.fromisoformat(license_data["expiry"])
                if datetime.now() > expiry:
                    self.logger.warning(f"License expired on {expiry}")
                    return False, {}
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid expiry date format: {e}")
                return False, {}

            # Check issued date (not in future)
            try:
                issued = datetime.fromisoformat(license_data["issued"])
                if issued > datetime.now():
                    self.logger.warning("License issued date is in the future")
                    return False, {}
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Invalid issued date format: {e}")
                return False, {}

            self.logger.info(
                f"License validated successfully for {license_data.get('customer')}"
            )
            return True, license_data

        except Exception as e:
            self.logger.error(f"Unexpected error validating license: {e}")
            return False, {}

    def get_license_info(self, license_key: str) -> Optional[Dict[str, Any]]:
        """
        Get license information if valid.

        Args:
            license_key: License key string

        Returns:
            Dictionary with license information, or None if invalid
        """
        is_valid, license_data = self.validate(license_key)
        return license_data if is_valid else None

    def check_feature(self, license_key: str, feature: str) -> bool:
        """
        Check if a specific feature is enabled in the license.

        Args:
            license_key: License key string
            feature: Feature name to check

        Returns:
            True if feature is enabled, False otherwise
        """
        is_valid, license_data = self.validate(license_key)
        if not is_valid:
            return False

        features = license_data.get("features", [])
        return feature in features

    def get_days_until_expiry(self, license_key: str) -> Optional[int]:
        """
        Get number of days until license expires.

        Args:
            license_key: License key string

        Returns:
            Number of days until expiry, or None if invalid/expired
        """
        is_valid, license_data = self.validate(license_key)
        if not is_valid:
            return None

        try:
            expiry = datetime.fromisoformat(license_data["expiry"])
            delta = expiry - datetime.now()
            return max(0, delta.days)
        except (ValueError, TypeError, KeyError):
            return None


class LicenseManager:
    """
    Manages license validation and enforcement at application startup.
    """

    def __init__(
        self, validator: LicenseValidator, logger: Optional[logging.Logger] = None
    ):
        """
        Initialize license manager.

        Args:
            validator: LicenseValidator instance
            logger: Logger instance
        """
        self.validator = validator
        self.logger = logger or logging.getLogger(__name__)
        self._license_data: Optional[Dict[str, Any]] = None

    def validate_startup_license(
        self, license_key: Optional[str], environment: str
    ) -> bool:
        """
        Validate license at application startup.

        Args:
            license_key: License key from configuration
            environment: Application environment (dev/staging/production)

        Returns:
            True if license is valid or not required, False otherwise
        """
        # Skip validation in development
        if environment == "dev":
            self.logger.info("License validation skipped in development mode")
            return True

        # Require license in production
        if environment == "production":
            if not license_key:
                self.logger.error("License key required for production environment")
                return False

            is_valid, license_data = self.validator.validate(license_key)
            if not is_valid:
                self.logger.error("Invalid or expired license key")
                return False

            self._license_data = license_data

            # Log license info
            days_left = self.validator.get_days_until_expiry(license_key)
            self.logger.info(
                f"License validated: {license_data.get('customer')} "
                f"(expires in {days_left} days)"
            )

            # Warn if expiring soon
            if days_left and days_left < 30:
                self.logger.warning(f"License expires in {days_left} days!")

            return True

        # Staging: validate if provided
        if license_key:
            is_valid, license_data = self.validator.validate(license_key)
            if is_valid:
                self._license_data = license_data
                self.logger.info("License validated for staging environment")
            else:
                self.logger.warning("Invalid license key in staging environment")

        return True

    def get_license_data(self) -> Optional[Dict[str, Any]]:
        """
        Get current license data.

        Returns:
            License data dictionary, or None if not validated
        """
        return self._license_data

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled in current license.

        Args:
            feature: Feature name

        Returns:
            True if enabled, False otherwise
        """
        if not self._license_data:
            return False

        features = self._license_data.get("features", [])
        return feature in features


def generate_license_key(
    private_key_pem: str,
    customer: str,
    email: str,
    expiry_date: str,
    features: list = None,
    max_users: int = 1,
) -> str:
    """
    Generate a license key (for license server use only).

    Args:
        private_key_pem: PEM-encoded RSA private key
        customer: Customer name
        email: Customer email
        expiry_date: Expiry date in ISO format (YYYY-MM-DD)
        features: List of enabled features
        max_users: Maximum number of users

    Returns:
        License key string

    Note:
        This function should only be used by the license server,
        not distributed with the application.
    """
    if not CRYPTO_AVAILABLE:
        raise ValidationError("Cryptography library not installed", "crypto_library")

    # Load private key
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )

    # Create payload
    payload_data = {
        "customer": customer,
        "email": email,
        "issued": datetime.now().isoformat(),
        "expiry": expiry_date,
        "features": features or [],
        "max_users": max_users,
    }

    payload = json.dumps(payload_data).encode("utf-8")

    # Sign payload
    signature = private_key.sign(
        payload,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    # Encode to base64
    payload_b64 = base64.b64encode(payload).decode("utf-8")
    signature_b64 = base64.b64encode(signature).decode("utf-8")

    return f"{payload_b64}.{signature_b64}"
