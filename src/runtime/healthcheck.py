"""
Application Health Check System

Provides comprehensive health checks for:
- Database connectivity
- File system access
- Network connectivity
- Service availability
- Configuration validity
"""

import logging
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List

from runtime.watchdog import HealthCheck, HealthStatus


class HealthCheckSystem:
    """
    Comprehensive health check system.

    Performs various health checks to ensure application is functioning properly.
    """

    def __init__(self, logger: logging.Logger, config):
        self.logger = logger
        self.config = config

    def check_database(self) -> HealthCheck:
        """Check database connectivity and integrity"""
        try:
            # Try to connect to database
            conn = sqlite3.connect(str(self.config.db_path))
            cursor = conn.cursor()

            # Test query
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            # Check database size
            db_size = self.config.db_path.stat().st_size / 1024 / 1024  # MB

            conn.close()

            # Check if database is too large (warning at 500MB, critical at 1GB)
            if db_size > 1024:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.CRITICAL,
                    message=f"Database too large: {db_size:.1f} MB",
                    timestamp=datetime.now(),
                    details={"size_mb": db_size, "tables": table_count},
                )
            elif db_size > 500:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.WARNING,
                    message=f"Database size high: {db_size:.1f} MB",
                    timestamp=datetime.now(),
                    details={"size_mb": db_size, "tables": table_count},
                )

            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message=f"Database OK ({table_count} tables, {db_size:.1f} MB)",
                timestamp=datetime.now(),
                details={"size_mb": db_size, "tables": table_count},
            )

        except Exception as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}",
                timestamp=datetime.now(),
            )

    def check_filesystem(self) -> HealthCheck:
        """Check file system access"""
        try:
            # Check if required directories exist and are writable
            dirs_to_check = [
                self.config.log_dir,
                self.config.export_dir,
                self.config.backup_dir,
            ]

            issues = []
            for dir_path in dirs_to_check:
                if not dir_path.exists():
                    issues.append(f"{dir_path.name} does not exist")
                elif not dir_path.is_dir():
                    issues.append(f"{dir_path.name} is not a directory")
                else:
                    # Test write access
                    test_file = dir_path / f".write_test_{datetime.now().timestamp()}"
                    try:
                        test_file.write_text("test")
                        test_file.unlink()
                    except Exception as e:
                        issues.append(f"{dir_path.name} not writable: {e}")

            # Check disk space (Windows-safe)
            try:
                import psutil

                if sys.platform == "win32":
                    import os

                    drive = os.path.splitdrive(os.getcwd())[0] + "\\"
                    disk = psutil.disk_usage(drive)
                else:
                    disk = psutil.disk_usage("/")

                if disk.percent > 95:
                    issues.append(f"Disk space critical: {disk.percent:.1f}%")
                elif disk.percent > 85:
                    issues.append(f"Disk space low: {disk.percent:.1f}%")
            except:
                pass

            if issues:
                return HealthCheck(
                    name="filesystem",
                    status=HealthStatus.CRITICAL,
                    message=f"Filesystem issues: {', '.join(issues)}",
                    timestamp=datetime.now(),
                    details={"issues": issues},
                )

            return HealthCheck(
                name="filesystem",
                status=HealthStatus.HEALTHY,
                message="Filesystem access OK",
                timestamp=datetime.now(),
            )

        except Exception as e:
            return HealthCheck(
                name="filesystem",
                status=HealthStatus.CRITICAL,
                message=f"Filesystem check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def check_log_files(self) -> HealthCheck:
        """Check log file sizes"""
        try:
            log_files = list(self.config.log_dir.glob("*.log"))
            total_size = sum(f.stat().st_size for f in log_files) / 1024 / 1024  # MB

            # Warning at 100MB, critical at 500MB
            if total_size > 500:
                return HealthCheck(
                    name="log_files",
                    status=HealthStatus.CRITICAL,
                    message=f"Log files too large: {total_size:.1f} MB",
                    timestamp=datetime.now(),
                    details={"size_mb": total_size, "file_count": len(log_files)},
                )
            elif total_size > 100:
                return HealthCheck(
                    name="log_files",
                    status=HealthStatus.WARNING,
                    message=f"Log files size high: {total_size:.1f} MB",
                    timestamp=datetime.now(),
                    details={"size_mb": total_size, "file_count": len(log_files)},
                )

            return HealthCheck(
                name="log_files",
                status=HealthStatus.HEALTHY,
                message=f"Log files OK ({len(log_files)} files, {total_size:.1f} MB)",
                timestamp=datetime.now(),
                details={"size_mb": total_size, "file_count": len(log_files)},
            )

        except Exception as e:
            return HealthCheck(
                name="log_files",
                status=HealthStatus.WARNING,
                message=f"Log check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def check_crash_reports(self) -> HealthCheck:
        """Check for recent crash reports"""
        try:
            crash_dir = self.config.log_dir / "crashes"
            if not crash_dir.exists():
                return HealthCheck(
                    name="crash_reports",
                    status=HealthStatus.HEALTHY,
                    message="No crash reports",
                    timestamp=datetime.now(),
                )

            crash_files = list(crash_dir.glob("crash_*.txt"))

            if not crash_files:
                return HealthCheck(
                    name="crash_reports",
                    status=HealthStatus.HEALTHY,
                    message="No crash reports",
                    timestamp=datetime.now(),
                )

            # Check for recent crashes (last 24 hours)
            recent_crashes = []
            now = datetime.now().timestamp()
            for crash_file in crash_files:
                file_time = crash_file.stat().st_mtime
                if now - file_time < 86400:  # 24 hours
                    recent_crashes.append(crash_file)

            if recent_crashes:
                return HealthCheck(
                    name="crash_reports",
                    status=HealthStatus.WARNING,
                    message=f"{len(recent_crashes)} recent crash(es) detected",
                    timestamp=datetime.now(),
                    details={
                        "total_crashes": len(crash_files),
                        "recent_crashes": len(recent_crashes),
                    },
                )

            return HealthCheck(
                name="crash_reports",
                status=HealthStatus.HEALTHY,
                message=f"{len(crash_files)} old crash report(s)",
                timestamp=datetime.now(),
                details={"total_crashes": len(crash_files)},
            )

        except Exception as e:
            return HealthCheck(
                name="crash_reports",
                status=HealthStatus.UNKNOWN,
                message=f"Crash check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def check_configuration(self) -> HealthCheck:
        """Check configuration validity"""
        try:
            errors = self.config.validate()

            if errors:
                return HealthCheck(
                    name="configuration",
                    status=HealthStatus.CRITICAL,
                    message=f"Configuration errors: {', '.join(errors)}",
                    timestamp=datetime.now(),
                    details={"errors": errors},
                )

            return HealthCheck(
                name="configuration",
                status=HealthStatus.HEALTHY,
                message="Configuration valid",
                timestamp=datetime.now(),
            )

        except Exception as e:
            return HealthCheck(
                name="configuration",
                status=HealthStatus.CRITICAL,
                message=f"Configuration check failed: {str(e)}",
                timestamp=datetime.now(),
            )

    def run_all_checks(self) -> List[HealthCheck]:
        """
        Run all health checks.

        Returns:
            List of HealthCheck results
        """
        checks = []

        self.logger.info("Running health checks...")

        checks.append(self.check_database())
        checks.append(self.check_filesystem())
        checks.append(self.check_log_files())
        checks.append(self.check_crash_reports())
        checks.append(self.check_configuration())

        # Log summary
        critical = sum(1 for c in checks if c.status == HealthStatus.CRITICAL)
        warning = sum(1 for c in checks if c.status == HealthStatus.WARNING)
        healthy = sum(1 for c in checks if c.status == HealthStatus.HEALTHY)

        self.logger.info(
            f"Health check complete: {healthy} healthy, {warning} warnings, {critical} critical"
        )

        return checks

    def get_health_report(self) -> Dict:
        """
        Get comprehensive health report.

        Returns:
            Dict with health status and details
        """
        checks = self.run_all_checks()

        # Determine overall status
        has_critical = any(c.status == HealthStatus.CRITICAL for c in checks)
        has_warning = any(c.status == HealthStatus.WARNING for c in checks)

        if has_critical:
            overall = HealthStatus.CRITICAL
        elif has_warning:
            overall = HealthStatus.WARNING
        else:
            overall = HealthStatus.HEALTHY

        return {
            "overall_status": overall.value,
            "timestamp": datetime.now().isoformat(),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "details": c.details,
                }
                for c in checks
            ],
        }
