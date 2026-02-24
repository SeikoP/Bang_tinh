"""
Application Watchdog

Monitors application health and detects:
- Deadlocks
- Frozen UI
- Memory leaks
- Unresponsive threads
- Resource exhaustion
"""

import logging
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class HealthStatus(Enum):
    """Health check status"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result"""

    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    details: Dict = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ApplicationWatchdog:
    """
    Application watchdog for monitoring health.

    Runs periodic health checks and can trigger alerts or recovery actions.
    """

    def __init__(
        self, logger: logging.Logger, check_interval: int = 60, enabled: bool = True
    ):
        self.logger = logger
        self.check_interval = check_interval
        self.enabled = enabled

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_heartbeat = datetime.now()
        self._health_checks: List[HealthCheck] = []
        self._custom_checks: List[Callable[[], HealthCheck]] = []
        self._lock = threading.Lock()  # Thread safety

        # Thresholds
        self.memory_warning_threshold = 80  # percent
        self.memory_critical_threshold = 95  # percent
        self.cpu_warning_threshold = 80  # percent
        self.cpu_critical_threshold = 95  # percent
        self.disk_warning_threshold = 85  # percent
        self.disk_critical_threshold = 95  # percent

    def start(self):
        """Start the watchdog"""
        if not self.enabled or self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="Watchdog")
        self._thread.start()

        self.logger.info(f"Watchdog started (interval: {self.check_interval}s)")

    def stop(self):
        """Stop the watchdog"""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

        self.logger.info("Watchdog stopped")

    def heartbeat(self):
        """Update heartbeat timestamp"""
        with self._lock:
            self._last_heartbeat = datetime.now()

    def register_check(self, check_func: Callable[[], HealthCheck]):
        """
        Register a custom health check function.

        Args:
            check_func: Function that returns a HealthCheck
        """
        self._custom_checks.append(check_func)
        self.logger.debug(f"Registered health check: {check_func.__name__}")

    def _run(self):
        """Main watchdog loop"""
        while self._running:
            try:
                # Run all health checks
                self._perform_health_checks()

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Watchdog error: {e}", exc_info=True)
                time.sleep(self.check_interval)

    def _perform_health_checks(self):
        """Perform all health checks"""
        checks = []

        # Built-in checks
        checks.append(self._check_heartbeat())
        checks.append(self._check_memory())
        checks.append(self._check_cpu())
        checks.append(self._check_disk())

        # Custom checks
        for check_func in self._custom_checks:
            try:
                result = check_func()
                checks.append(result)
            except Exception as e:
                self.logger.error(f"Custom health check failed: {e}")
                checks.append(
                    HealthCheck(
                        name=check_func.__name__,
                        status=HealthStatus.UNKNOWN,
                        message=f"Check failed: {str(e)}",
                        timestamp=datetime.now(),
                    )
                )

        # Store results (thread-safe)
        with self._lock:
            self._health_checks = checks

        # Log warnings and critical issues
        for check in checks:
            if check.status == HealthStatus.CRITICAL:
                self.logger.error(f"CRITICAL: {check.name} - {check.message}")
            elif check.status == HealthStatus.WARNING:
                self.logger.warning(f"WARNING: {check.name} - {check.message}")

    def _check_heartbeat(self) -> HealthCheck:
        """Check if application is responsive"""
        with self._lock:
            last_heartbeat = self._last_heartbeat

        time_since_heartbeat = datetime.now() - last_heartbeat

        if time_since_heartbeat > timedelta(minutes=5):
            return HealthCheck(
                name="heartbeat",
                status=HealthStatus.CRITICAL,
                message=f"No heartbeat for {time_since_heartbeat.total_seconds():.0f}s",
                timestamp=datetime.now(),
                details={"last_heartbeat": last_heartbeat.isoformat()},
            )
        elif time_since_heartbeat > timedelta(minutes=2):
            return HealthCheck(
                name="heartbeat",
                status=HealthStatus.WARNING,
                message=f"Heartbeat delayed: {time_since_heartbeat.total_seconds():.0f}s",
                timestamp=datetime.now(),
                details={"last_heartbeat": last_heartbeat.isoformat()},
            )

        return HealthCheck(
            name="heartbeat",
            status=HealthStatus.HEALTHY,
            message="Heartbeat normal",
            timestamp=datetime.now(),
        )

    def _check_memory(self) -> HealthCheck:
        """Check memory usage"""
        if not HAS_PSUTIL:
            return HealthCheck(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
                timestamp=datetime.now(),
            )

        try:
            mem = psutil.virtual_memory()
            percent = mem.percent

            if percent >= self.memory_critical_threshold:
                return HealthCheck(
                    name="memory",
                    status=HealthStatus.CRITICAL,
                    message=f"Memory usage critical: {percent:.1f}%",
                    timestamp=datetime.now(),
                    details={
                        "percent": percent,
                        "used_gb": mem.used / 1024 / 1024 / 1024,
                        "total_gb": mem.total / 1024 / 1024 / 1024,
                    },
                )
            elif percent >= self.memory_warning_threshold:
                return HealthCheck(
                    name="memory",
                    status=HealthStatus.WARNING,
                    message=f"Memory usage high: {percent:.1f}%",
                    timestamp=datetime.now(),
                    details={"percent": percent},
                )

            return HealthCheck(
                name="memory",
                status=HealthStatus.HEALTHY,
                message=f"Memory usage normal: {percent:.1f}%",
                timestamp=datetime.now(),
                details={"percent": percent},
            )

        except Exception as e:
            return HealthCheck(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check memory: {str(e)}",
                timestamp=datetime.now(),
            )

    def _check_cpu(self) -> HealthCheck:
        """Check CPU usage"""
        if not HAS_PSUTIL:
            return HealthCheck(
                name="cpu",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
                timestamp=datetime.now(),
            )

        try:
            percent = psutil.cpu_percent(interval=1)

            if percent >= self.cpu_critical_threshold:
                return HealthCheck(
                    name="cpu",
                    status=HealthStatus.CRITICAL,
                    message=f"CPU usage critical: {percent:.1f}%",
                    timestamp=datetime.now(),
                    details={"percent": percent},
                )
            elif percent >= self.cpu_warning_threshold:
                return HealthCheck(
                    name="cpu",
                    status=HealthStatus.WARNING,
                    message=f"CPU usage high: {percent:.1f}%",
                    timestamp=datetime.now(),
                    details={"percent": percent},
                )

            return HealthCheck(
                name="cpu",
                status=HealthStatus.HEALTHY,
                message=f"CPU usage normal: {percent:.1f}%",
                timestamp=datetime.now(),
                details={"percent": percent},
            )

        except Exception as e:
            return HealthCheck(
                name="cpu",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check CPU: {str(e)}",
                timestamp=datetime.now(),
            )

    def _check_disk(self) -> HealthCheck:
        """Check disk space"""
        if not HAS_PSUTIL:
            return HealthCheck(
                name="disk",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
                timestamp=datetime.now(),
            )

        try:
            # Windows-safe disk check
            if sys.platform == "win32":
                import os

                drive = os.path.splitdrive(os.getcwd())[0] + "\\"
                disk = psutil.disk_usage(drive)
            else:
                disk = psutil.disk_usage("/")

            percent = disk.percent

            if percent >= self.disk_critical_threshold:
                return HealthCheck(
                    name="disk",
                    status=HealthStatus.CRITICAL,
                    message=f"Disk space critical: {percent:.1f}%",
                    timestamp=datetime.now(),
                    details={
                        "percent": percent,
                        "free_gb": disk.free / 1024 / 1024 / 1024,
                    },
                )
            elif percent >= self.disk_warning_threshold:
                return HealthCheck(
                    name="disk",
                    status=HealthStatus.WARNING,
                    message=f"Disk space low: {percent:.1f}%",
                    timestamp=datetime.now(),
                    details={"percent": percent},
                )

            return HealthCheck(
                name="disk",
                status=HealthStatus.HEALTHY,
                message=f"Disk space normal: {percent:.1f}%",
                timestamp=datetime.now(),
                details={"percent": percent},
            )

        except Exception as e:
            return HealthCheck(
                name="disk",
                status=HealthStatus.UNKNOWN,
                message=f"Failed to check disk: {str(e)}",
                timestamp=datetime.now(),
            )

    def get_health_status(self) -> Dict:
        """
        Get current health status.

        Returns:
            Dict with overall status and individual checks
        """
        if not self._health_checks:
            return {
                "overall": HealthStatus.UNKNOWN.value,
                "checks": [],
                "timestamp": datetime.now().isoformat(),
            }

        # Determine overall status
        has_critical = any(
            c.status == HealthStatus.CRITICAL for c in self._health_checks
        )
        has_warning = any(c.status == HealthStatus.WARNING for c in self._health_checks)

        if has_critical:
            overall = HealthStatus.CRITICAL
        elif has_warning:
            overall = HealthStatus.WARNING
        else:
            overall = HealthStatus.HEALTHY

        return {
            "overall": overall.value,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "timestamp": c.timestamp.isoformat(),
                    "details": c.details,
                }
                for c in self._health_checks
            ],
            "timestamp": datetime.now().isoformat(),
        }
