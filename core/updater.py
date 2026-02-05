"""Secure update mechanism with signature verification"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.exceptions import InvalidSignature

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

from core.exceptions import AppException, ValidationError


class UpdateInfo:
    """Information about an available update"""

    def __init__(
        self,
        version: str,
        download_url: str,
        signature_url: str,
        release_notes: str,
        file_size: int,
        checksum: str,
    ):
        """
        Initialize update information.

        Args:
            version: Version string (e.g., "2.1.0")
            download_url: URL to download update package
            signature_url: URL to download signature file
            release_notes: Release notes text
            file_size: File size in bytes
            checksum: SHA256 checksum of update file
        """
        self.version = version
        self.download_url = download_url
        self.signature_url = signature_url
        self.release_notes = release_notes
        self.file_size = file_size
        self.checksum = checksum

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UpdateInfo":
        """Create UpdateInfo from dictionary"""
        return cls(
            version=data["version"],
            download_url=data["download_url"],
            signature_url=data["signature_url"],
            release_notes=data.get("release_notes", ""),
            file_size=data.get("file_size", 0),
            checksum=data.get("checksum", ""),
        )


class SecureUpdater:
    """
    Secure application updater with cryptographic signature verification.

    Update process:
    1. Check for updates from update server
    2. Download update package
    3. Download signature file
    4. Verify signature using public key
    5. Verify checksum
    6. Apply update
    """

    # Default public key for update verification (replace with real key)
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
        current_version: str,
        update_server_url: str,
        public_key_pem: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize secure updater.

        Args:
            current_version: Current application version
            update_server_url: Base URL of update server
            public_key_pem: PEM-encoded RSA public key for signature verification
            logger: Logger instance

        Raises:
            ValidationError: If cryptography library not available
        """
        if not CRYPTO_AVAILABLE:
            raise ValidationError(
                "Cryptography library not installed. Install with: pip install cryptography",
                "crypto_library",
            )

        self.current_version = current_version
        self.update_server_url = update_server_url.rstrip("/")
        self.logger = logger or logging.getLogger(__name__)

        # Load public key
        pem_data = public_key_pem or self.DEFAULT_PUBLIC_KEY_PEM
        try:
            self.public_key = serialization.load_pem_public_key(
                pem_data.encode("utf-8")
            )
            self.logger.info("Updater initialized with public key")
        except Exception as e:
            self.logger.error(f"Failed to load public key: {e}")
            raise ValidationError("Invalid public key format", "public_key") from e

    def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Check if updates are available.

        Returns:
            UpdateInfo if update available, None otherwise

        Raises:
            AppException: If update check fails
        """
        try:
            # Request update information from server
            url = f"{self.update_server_url}/api/updates/latest"
            request = Request(
                url,
                headers={
                    "User-Agent": f"WarehouseApp/{self.current_version}",
                    "Accept": "application/json",
                },
            )

            self.logger.info(f"Checking for updates at {url}")

            with urlopen(request, timeout=10) as response:
                if response.status != 200:
                    raise AppException(
                        f"Update server returned status {response.status}",
                        "UPDATE_CHECK_ERROR",
                    )

                data = json.loads(response.read().decode("utf-8"))

            # Parse update information
            latest_version = data.get("version")
            if not latest_version:
                self.logger.warning("No version information in update response")
                return None

            # Compare versions
            if self._is_newer_version(latest_version, self.current_version):
                self.logger.info(f"Update available: {latest_version}")
                return UpdateInfo.from_dict(data)
            else:
                self.logger.info("Application is up to date")
                return None

        except (URLError, HTTPError) as e:
            self.logger.error(f"Failed to check for updates: {e}")
            raise AppException(
                "Cannot connect to update server",
                "UPDATE_CHECK_ERROR",
                {"error": str(e)},
            ) from e
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid update response format: {e}")
            raise AppException(
                "Invalid update server response",
                "UPDATE_CHECK_ERROR",
                {"error": str(e)},
            ) from e

    def download_and_verify_update(
        self, update_info: UpdateInfo, download_dir: Optional[Path] = None
    ) -> Path:
        """
        Download update package and verify its signature.

        Args:
            update_info: Update information
            download_dir: Directory to download to (uses temp if None)

        Returns:
            Path to verified update file

        Raises:
            AppException: If download or verification fails
        """
        if download_dir is None:
            download_dir = Path(tempfile.gettempdir()) / "warehouse_updates"

        download_dir.mkdir(parents=True, exist_ok=True)

        update_file = download_dir / f"update_{update_info.version}.exe"
        signature_file = download_dir / f"update_{update_info.version}.sig"

        try:
            # Download update file
            self.logger.info(f"Downloading update from {update_info.download_url}")
            self._download_file(update_info.download_url, update_file)

            # Download signature file
            self.logger.info(f"Downloading signature from {update_info.signature_url}")
            self._download_file(update_info.signature_url, signature_file)

            # Verify checksum
            if update_info.checksum:
                self.logger.info("Verifying checksum...")
                if not self._verify_checksum(update_file, update_info.checksum):
                    raise AppException(
                        "Update file checksum verification failed",
                        "UPDATE_VERIFICATION_ERROR",
                    )

            # Verify signature
            self.logger.info("Verifying signature...")
            if not self._verify_signature(update_file, signature_file):
                raise AppException(
                    "Update file signature verification failed",
                    "UPDATE_VERIFICATION_ERROR",
                )

            self.logger.info("Update verified successfully")
            return update_file

        except Exception as e:
            # Clean up on failure
            if update_file.exists():
                update_file.unlink()
            if signature_file.exists():
                signature_file.unlink()
            raise

    def apply_update(self, update_file: Path) -> bool:
        """
        Apply the verified update.

        Args:
            update_file: Path to verified update file

        Returns:
            True if update applied successfully

        Note:
            This typically involves launching the installer and exiting the application.
        """
        try:
            self.logger.info(f"Applying update from {update_file}")

            # Launch installer
            import subprocess

            subprocess.Popen([str(update_file), "/SILENT"])

            self.logger.info("Update installer launched")
            return True

        except Exception as e:
            self.logger.error(f"Failed to apply update: {e}")
            raise AppException(
                "Failed to apply update", "UPDATE_APPLY_ERROR", {"error": str(e)}
            ) from e

    def _download_file(self, url: str, destination: Path) -> None:
        """
        Download file from URL.

        Args:
            url: URL to download from
            destination: Path to save file

        Raises:
            AppException: If download fails
        """
        try:
            request = Request(
                url, headers={"User-Agent": f"WarehouseApp/{self.current_version}"}
            )

            with urlopen(request, timeout=300) as response:
                if response.status != 200:
                    raise AppException(
                        f"Download failed with status {response.status}",
                        "DOWNLOAD_ERROR",
                    )

                with open(destination, "wb") as f:
                    shutil.copyfileobj(response, f)

        except (URLError, HTTPError) as e:
            raise AppException(
                f"Failed to download from {url}", "DOWNLOAD_ERROR", {"error": str(e)}
            ) from e

    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verify file checksum.

        Args:
            file_path: Path to file
            expected_checksum: Expected SHA256 checksum (hex)

        Returns:
            True if checksum matches, False otherwise
        """
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)

            actual_checksum = sha256.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()

        except Exception as e:
            self.logger.error(f"Checksum verification error: {e}")
            return False

    def _verify_signature(self, file_path: Path, signature_path: Path) -> bool:
        """
        Verify file signature using RSA public key.

        Args:
            file_path: Path to file to verify
            signature_path: Path to signature file

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Read file content
            with open(file_path, "rb") as f:
                file_data = f.read()

            # Read signature
            with open(signature_path, "rb") as f:
                signature = f.read()

            # Verify signature
            try:
                self.public_key.verify(
                    signature,
                    file_data,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
                return True
            except InvalidSignature:
                self.logger.warning("Signature verification failed")
                return False

        except Exception as e:
            self.logger.error(f"Signature verification error: {e}")
            return False

    def _is_newer_version(self, version1: str, version2: str) -> bool:
        """
        Compare version strings.

        Args:
            version1: First version string (e.g., "2.1.0")
            version2: Second version string (e.g., "2.0.0")

        Returns:
            True if version1 is newer than version2
        """
        try:
            v1_parts = [int(x) for x in version1.split(".")]
            v2_parts = [int(x) for x in version2.split(".")]

            # Pad with zeros if needed
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts += [0] * (max_len - len(v1_parts))
            v2_parts += [0] * (max_len - len(v2_parts))

            return v1_parts > v2_parts

        except (ValueError, AttributeError):
            self.logger.warning(f"Invalid version format: {version1} or {version2}")
            return False


class UpdateManager:
    """
    Manages update checking and application at startup.
    """

    def __init__(self, updater: SecureUpdater, logger: Optional[logging.Logger] = None):
        """
        Initialize update manager.

        Args:
            updater: SecureUpdater instance
            logger: Logger instance
        """
        self.updater = updater
        self.logger = logger or logging.getLogger(__name__)

    def check_updates_on_startup(
        self, auto_download: bool = False
    ) -> Optional[UpdateInfo]:
        """
        Check for updates at application startup.

        Args:
            auto_download: If True, automatically download updates

        Returns:
            UpdateInfo if update available, None otherwise
        """
        try:
            update_info = self.updater.check_for_updates()

            if update_info:
                self.logger.info(
                    f"Update available: {update_info.version} "
                    f"(current: {self.updater.current_version})"
                )

                if auto_download:
                    self.logger.info("Auto-downloading update...")
                    update_file = self.updater.download_and_verify_update(update_info)
                    self.logger.info(f"Update downloaded and verified: {update_file}")

                return update_info

            return None

        except Exception as e:
            self.logger.error(f"Update check failed: {e}")
            # Don't block application startup on update check failure
            return None
