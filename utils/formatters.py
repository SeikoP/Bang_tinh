"""
Formatters - Các hàm format và parse dữ liệu
"""
import re
from datetime import datetime, date
from typing import Union


def parse_to_small_units(value_str: str, conversion: int) -> int:
    """
    Parse chuỗi input thành đơn vị nhỏ.
    
    Hỗ trợ nhiều định dạng:
    - "3.4" -> 3 đơn vị lớn + 4 đơn vị nhỏ
    - "3t4" -> tương tự (t = thùng, v = vỉ, g = gói, k = két)
    - "3" -> 3 đơn vị lớn
    
    Args:
        value_str: Chuỗi input từ người dùng
        conversion: Số đơn vị nhỏ trong 1 đơn vị lớn
        
    Returns:
        Tổng số đơn vị nhỏ
    """
    if not value_str:
        return 0
    
    value_str = str(value_str).strip().lower()
    
    # Thay thế các ký tự chữ cái bằng dấu chấm để chuẩn hóa
    normalized = re.sub(r'[a-z]', '.', value_str)
    
    try:
        if "." in normalized:
            parts = normalized.split(".")
            large = int(parts[0]) if parts[0] and parts[0].isdigit() else 0
            small = int(parts[1]) if len(parts) > 1 and parts[1] and parts[1].isdigit() else 0
            return (large * conversion) + small
        else:
            # Chỉ có một số -> hiểu là đơn vị lớn
            if normalized.isdigit():
                return int(normalized) * conversion
            return 0
    except ValueError:
        return 0


def format_to_display(total_small_units: int, conversion: int, unit_char: str) -> str:
    """
    Format số đơn vị nhỏ thành chuỗi hiển thị đẹp.
    
    Example: 76 đơn vị nhỏ, conversion=24, unit_char='t' -> "3t4"
    
    Args:
        total_small_units: Tổng số đơn vị nhỏ
        conversion: Số đơn vị nhỏ trong 1 đơn vị lớn
        unit_char: Ký tự viết tắt của đơn vị lớn
        
    Returns:
        Chuỗi định dạng "XuY" (X đơn vị lớn, Y đơn vị nhỏ)
    """
    if total_small_units < 0:
        return "0"
    
    large = total_small_units // conversion
    small = total_small_units % conversion
    
    if small == 0:
        return f"{large}{unit_char}"
    return f"{large}{unit_char}{small}"


def normalize_input(value_str: str, conversion: int) -> int:
    """
    Chuẩn hóa input từ người dùng.
    Wrapper function cho parse_to_small_units.
    
    Args:
        value_str: Chuỗi input
        conversion: Tỉ lệ quy đổi
        
    Returns:
        Số đơn vị nhỏ
    """
    return parse_to_small_units(value_str, conversion)


def format_currency(amount: Union[int, float], symbol: str = "đ") -> str:
    """
    Format số tiền theo định dạng Việt Nam.
    
    Example: 1500000 -> "1,500,000 đ"
    
    Args:
        amount: Số tiền
        symbol: Ký hiệu tiền tệ
        
    Returns:
        Chuỗi số tiền đã format
    """
    return f"{amount:,.0f} {symbol}"


def format_date(d: Union[date, datetime, str]) -> str:
    """
    Format ngày theo định dạng dd/mm/yyyy.
    
    Args:
        d: Ngày cần format (date, datetime hoặc string ISO)
        
    Returns:
        Chuỗi ngày đã format
    """
    if isinstance(d, str):
        d = datetime.fromisoformat(d).date() if 'T' in d else date.fromisoformat(d)
    if isinstance(d, datetime):
        d = d.date()
    return d.strftime("%d/%m/%Y")


def format_datetime(dt: Union[datetime, str]) -> str:
    """
    Format datetime theo định dạng dd/mm/yyyy HH:MM.
    
    Args:
        dt: Datetime cần format
        
    Returns:
        Chuỗi datetime đã format
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime("%d/%m/%Y %H:%M")
