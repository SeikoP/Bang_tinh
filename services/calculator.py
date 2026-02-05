"""
Calculator Service - Business logic cho tính toán
"""
import re
from typing import Tuple
from database import SessionRepository, SessionData


class CalculatorService:
    """Service xử lý logic tính toán"""
    
    @staticmethod
    def parse_to_small_units(value_str: str, conversion: int) -> int:
        """
        Parse chuỗi input thành đơn vị nhỏ.
        
        Examples:
            - "3.4" với conversion=24 -> 3*24 + 4 = 76
            - "3t4" với conversion=24 -> 76
            - "3" với conversion=24 -> 72 (tự hiểu là 3 đơn vị lớn)
        """
        if not value_str:
            return 0
        
        value_str = str(value_str).strip().lower()
        
        # Thay thế ký tự chữ bằng dấu chấm
        normalized = re.sub(r'[a-z]', '.', value_str)
        
        try:
            if "." in normalized:
                parts = normalized.split(".")
                large = int(parts[0]) if parts[0] and parts[0].isdigit() else 0
                small = int(parts[1]) if len(parts) > 1 and parts[1] and parts[1].isdigit() else 0
                return (large * conversion) + small
            else:
                if normalized.isdigit():
                    return int(normalized) * conversion
                return 0
        except ValueError:
            return 0
    
    @staticmethod
    def format_to_display(total_small_units: int, conversion: int, unit_char: str) -> str:
        """
        Format số đơn vị nhỏ thành chuỗi hiển thị.
        
        Example: 76, 24, 't' -> "3t4"
        """
        if total_small_units < 0:
            return "0"
        
        large = total_small_units // conversion
        small = total_small_units % conversion
        
        if small == 0:
            return f"{large}{unit_char}"
        return f"{large}{unit_char}{small}"
    
    @staticmethod
    def calculate_used(handover: int, closing: int) -> int:
        """Tính số lượng đã sử dụng"""
        return max(0, handover - closing)
    
    @staticmethod
    def calculate_amount(used_qty: int, unit_price: float) -> float:
        """Tính thành tiền"""
        return used_qty * unit_price
    
    @staticmethod
    def get_session_total() -> float:
        """Tính tổng tiền phiên hiện tại"""
        return SessionRepository.get_total_amount()
    
    @staticmethod
    def validate_closing_qty(handover: int, closing: int) -> Tuple[bool, str]:
        """
        Validate số lượng chốt ca.
        Returns: (is_valid, error_message)
        """
        if closing < 0:
            return False, "Số lượng không thể âm"
        if closing > handover:
            return False, "Chốt ca không thể lớn hơn giao ca"
        return True, ""
    
    @staticmethod
    def normalize_input(value_str: str, conversion: int) -> int:
        """
        Chuẩn hóa input.
        Chuyển đổi input người dùng thành số đơn vị nhỏ.
        """
        return CalculatorService.parse_to_small_units(value_str, conversion)
