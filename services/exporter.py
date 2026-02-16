"""
Export Service - Xuất báo cáo PDF và Excel
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from config import EXPORT_DATE_FORMAT, EXPORT_DIR
from core.exceptions import AppException, ValidationError
from database import (HistoryRepository, SessionData, SessionHistory,
                      SessionRepository)


class ExportService:
    """Service xuất báo cáo với error handling và logging"""

    def __init__(self, export_dir: Optional[Path] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize export service with dependencies.

        Args:
            export_dir: Directory for export files (defaults to EXPORT_DIR from config)
            logger: Logger instance for operation logging
        """
        self.export_dir = export_dir or EXPORT_DIR
        self.logger = logger or logging.getLogger(__name__)

        # Tạo thư mục export nếu chưa có
        try:
            Path(self.export_dir).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Export directory initialized: {self.export_dir}")
        except OSError as e:
            self.logger.error(f"Failed to create export directory: {e}")
            raise AppException(
                f"Cannot create export directory: {self.export_dir}",
                "EXPORT_DIR_ERROR",
                {"path": str(self.export_dir), "error": str(e)},
            ) from e

    def export_current_session_to_text(self, filename: Optional[str] = None) -> str:
        """
        Xuất phiên hiện tại ra file text.

        Args:
            filename: Optional custom filename

        Returns:
            Đường dẫn file đã xuất

        Raises:
            AppException: If export fails
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime(EXPORT_DATE_FORMAT)
                filename = f"phien_{timestamp}.txt"

            # Validate filename
            if not self._is_valid_filename(filename):
                raise ValidationError("Invalid filename", "filename")

            filepath = self.export_dir / filename

            # Validate export path permissions
            if not self._check_write_permission(self.export_dir):
                raise AppException(
                    f"No write permission for export directory: {self.export_dir}",
                    "PERMISSION_ERROR",
                )

            sessions = SessionRepository.get_all()
            total = sum(s.amount for s in sessions)

            content = self._generate_text_report(sessions, total, "Phiên hiện tại")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Exported current session to: {filepath}")
            return str(filepath)

        except (OSError, IOError) as e:
            self.logger.error(f"Failed to export current session: {e}")
            raise AppException(
                "Failed to export session to file",
                "EXPORT_ERROR",
                {"filename": filename, "error": str(e)},
            ) from e

    def export_history_to_text(
        self, history_id: int, filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Xuất lịch sử phiên ra file text.

        Args:
            history_id: ID of history record to export
            filename: Optional custom filename

        Returns:
            Đường dẫn file hoặc None nếu không tìm thấy

        Raises:
            AppException: If export fails
            ValidationError: If history_id is invalid
        """
        try:
            if history_id <= 0:
                raise ValidationError("History ID must be positive", "history_id")

            history = HistoryRepository.get_by_id(history_id)
            if not history:
                self.logger.warning(f"History not found: {history_id}")
                return None

            if not filename:
                timestamp = datetime.now().strftime(EXPORT_DATE_FORMAT)
                filename = f"lichsu_{history_id}_{timestamp}.txt"

            # Validate filename
            if not self._is_valid_filename(filename):
                raise ValidationError("Invalid filename", "filename")

            filepath = self.export_dir / filename

            content = self._generate_history_text_report(history)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            self.logger.info(f"Exported history {history_id} to: {filepath}")
            return str(filepath)

        except (OSError, IOError) as e:
            self.logger.error(f"Failed to export history {history_id}: {e}")
            raise AppException(
                "Failed to export history to file",
                "EXPORT_ERROR",
                {"history_id": history_id, "filename": filename, "error": str(e)},
            ) from e

    def _generate_text_report(
        self, sessions: List[SessionData], total: float, title: str
    ) -> str:
        """Generate nội dung báo cáo text"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  {title.upper()}")
        lines.append(f"  Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(
            f"{'STT':<5} {'Sản phẩm':<20} {'Giao':<10} {'Chốt':<10} {'Dùng':<8} {'Tiền':>12}"
        )
        lines.append("-" * 65)

        for i, s in enumerate(sessions, 1):
            lines.append(
                f"{i:<5} {s.product.name:<20} {s.handover_qty:<10} {s.closing_qty:<10} "
                f"{s.used_qty:<8} {s.amount:>12,.0f}"
            )

        lines.append("-" * 65)
        lines.append(f"{'TỔNG CỘNG':<54} {total:>12,.0f} VNĐ")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _generate_history_text_report(self, history: SessionHistory) -> str:
        """Generate nội dung báo cáo lịch sử"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  LỊCH SỬ PHIÊN #{history.id}")
        lines.append(f"  Ngày: {history.session_date}")
        if history.shift_name:
            lines.append(f"  Ca: {history.shift_name}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(
            f"{'STT':<5} {'Sản phẩm':<20} {'Giao':<10} {'Chốt':<10} {'Dùng':<8} {'Tiền':>12}"
        )
        lines.append("-" * 65)

        for i, item in enumerate(history.items, 1):
            lines.append(
                f"{i:<5} {item.product_name:<20} {item.handover_qty:<10} {item.closing_qty:<10} "
                f"{item.used_qty:<8} {item.amount:>12,.0f}"
            )

        lines.append("-" * 65)
        lines.append(f"{'TỔNG CỘNG':<54} {history.total_amount:>12,.0f} VNĐ")

        if history.notes:
            lines.append("")
            lines.append(f"Ghi chú: {history.notes}")

        lines.append("=" * 60)

        return "\n".join(lines)

    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Xuất phiên hiện tại ra file CSV.

        Args:
            filename: Optional custom filename

        Returns:
            Đường dẫn file đã xuất

        Raises:
            AppException: If export fails
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime(EXPORT_DATE_FORMAT)
                filename = f"phien_{timestamp}.csv"

            # Validate filename
            if not self._is_valid_filename(filename):
                raise ValidationError("Invalid filename", "filename")

            filepath = self.export_dir / filename
            sessions = SessionRepository.get_all()

            lines = [
                "STT,Sản phẩm,Đơn vị,Quy đổi,Đơn giá,Giao ca,Chốt ca,Đã dùng,Thành tiền"
            ]

            for i, s in enumerate(sessions, 1):
                lines.append(
                    f"{i},{s.product.name},{s.product.large_unit},{s.product.conversion},"
                    f"{s.product.unit_price},{s.handover_qty},{s.closing_qty},"
                    f"{s.used_qty},{s.amount}"
                )

            total = sum(s.amount for s in sessions)
            lines.append(f",,,,,,,,{total}")

            with open(filepath, "w", encoding="utf-8-sig") as f:
                f.write("\n".join(lines))

            self.logger.info(f"Exported session to CSV: {filepath}")
            return str(filepath)

        except (OSError, IOError) as e:
            self.logger.error(f"Failed to export to CSV: {e}")
            raise AppException(
                "Failed to export to CSV file",
                "EXPORT_ERROR",
                {"filename": filename, "error": str(e)},
            ) from e

    def _is_valid_filename(self, filename: str) -> bool:
        """
        Validate filename for security.

        Args:
            filename: Filename to validate

        Returns:
            True if valid, False otherwise
        """
        if not filename:
            return False

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            self.logger.warning(f"Invalid filename detected: {filename}")
            return False

        # Check for reasonable length
        if len(filename) > 255:
            return False

        return True

    def _check_write_permission(self, directory: Path) -> bool:
        """
        Check if directory has write permission.

        Args:
            directory: Directory path to check

        Returns:
            True if writable, False otherwise
        """
        try:
            test_file = directory / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, IOError):
            return False
