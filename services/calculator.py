"""
Calculator Service - Business logic cho tính toán
"""

import re
from typing import Optional, Tuple

from core.exceptions import ValidationError
from core.interfaces import ISessionRepository


class CalculatorService:
    """Service xử lý logic tính toán với dependency injection"""

    def __init__(self, session_repository: Optional[ISessionRepository] = None):
        """
        Initialize calculator service with dependencies.

        Args:
            session_repository: Repository for session data access (optional for stateless operations)
        """
        self._session_repo = session_repository

    def parse_to_small_units(self, value_str: str, conversion: int) -> int:
        """
        Parse chuỗi input thành đơn vị nhỏ.

        Examples:
            - "3.4" với conversion=24 -> 3*24 + 4 = 76
            - "3t4" với conversion=24 -> 76
            - "3" với conversion=24 -> 72 (tự hiểu là 3 đơn vị lớn)

        Args:
            value_str: Input string to parse
            conversion: Conversion factor (units per large unit)

        Returns:
            Total small units

        Raises:
            ValidationError: If conversion is invalid
        """
        # Validate conversion factor
        if conversion <= 0:
            raise ValidationError("Conversion factor must be positive", "conversion")

        if not value_str:
            return 0

        value_str = str(value_str).strip().lower()

        # Thay thế ký tự chữ bằng dấu chấm
        normalized = re.sub(r"[a-z]", ".", value_str)

        try:
            if "." in normalized:
                parts = normalized.split(".")
                large = int(parts[0]) if parts[0] and parts[0].isdigit() else 0
                small = (
                    int(parts[1])
                    if len(parts) > 1 and parts[1] and parts[1].isdigit()
                    else 0
                )

                # Validate small units don't exceed conversion
                if small >= conversion:
                    raise ValidationError(
                        f"Small units ({small}) cannot exceed conversion factor ({conversion})",
                        "value_str",
                    )

                return (large * conversion) + small
            else:
                if normalized.isdigit():
                    return int(normalized) * conversion
                return 0
        except ValueError as e:
            raise ValidationError(
                f"Invalid numeric format: {value_str}", "value_str"
            ) from e

    def format_to_display(
        self, total_small_units: int, conversion: int, unit_char: str
    ) -> str:
        """
        Format số đơn vị nhỏ thành chuỗi hiển thị.

        Example: 76, 24, 't' -> "3t4"

        Args:
            total_small_units: Total units in small denomination
            conversion: Conversion factor
            unit_char: Character representing the large unit

        Returns:
            Formatted display string

        Raises:
            ValidationError: If inputs are invalid
        """
        if conversion <= 0:
            raise ValidationError("Conversion factor must be positive", "conversion")

        if total_small_units < 0:
            return "0"

        large = total_small_units // conversion
        small = total_small_units % conversion

        if small == 0:
            return f"{large}{unit_char}"
        return f"{large}{unit_char}{small}"

    def calculate_used(self, handover: int, closing: int) -> int:
        """
        Tính số lượng đã sử dụng

        Args:
            handover: Handover quantity
            closing: Closing quantity

        Returns:
            Used quantity

        Raises:
            ValidationError: If quantities are invalid
        """
        if handover < 0:
            raise ValidationError("Handover quantity cannot be negative", "handover")
        if closing < 0:
            raise ValidationError("Closing quantity cannot be negative", "closing")
        if closing > handover:
            raise ValidationError(
                "Closing quantity cannot exceed handover quantity", "closing"
            )

        return max(0, handover - closing)

    def calculate_amount(self, used_qty: int, unit_price: float) -> float:
        """
        Tính thành tiền

        Args:
            used_qty: Used quantity
            unit_price: Price per unit

        Returns:
            Total amount

        Raises:
            ValidationError: If inputs are invalid
        """
        if used_qty < 0:
            raise ValidationError("Used quantity cannot be negative", "used_qty")
        if unit_price < 0:
            raise ValidationError("Unit price cannot be negative", "unit_price")

        return used_qty * unit_price

    def get_session_total(self) -> float:
        """
        Tính tổng tiền phiên hiện tại

        Returns:
            Total session amount

        Raises:
            ValidationError: If session repository not configured
        """
        if not self._session_repo:
            raise ValidationError(
                "Session repository not configured for this calculator instance",
                "session_repository",
            )

        return self._session_repo.get_total_amount()

    def validate_closing_qty(self, handover: int, closing: int) -> Tuple[bool, str]:
        """
        Validate số lượng chốt ca.

        Args:
            handover: Handover quantity
            closing: Closing quantity

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if closing < 0:
                return False, "Số lượng không thể âm"
            if closing > handover:
                return False, "Chốt ca không thể lớn hơn giao ca"
            return True, ""
        except Exception as e:
            return False, str(e)

    def normalize_input(self, value_str: str, conversion: int) -> int:
        """
        Chuẩn hóa input.
        Chuyển đổi input người dùng thành số đơn vị nhỏ.

        Args:
            value_str: Input string
            conversion: Conversion factor

        Returns:
            Normalized value in small units
        """
        return self.parse_to_small_units(value_str, conversion)
