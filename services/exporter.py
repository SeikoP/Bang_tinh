"""
Export Service - Xuất báo cáo PDF và Excel
"""
import os
from datetime import datetime, date
from typing import List, Optional
from pathlib import Path

# Import config
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EXPORT_DIR, EXPORT_DATE_FORMAT

from database import SessionRepository, HistoryRepository, SessionData, SessionHistory


class ExportService:
    """Service xuất báo cáo"""
    
    def __init__(self):
        # Tạo thư mục export nếu chưa có
        os.makedirs(EXPORT_DIR, exist_ok=True)
    
    def export_current_session_to_text(self, filename: str = None) -> str:
        """
        Xuất phiên hiện tại ra file text.
        Trả về đường dẫn file.
        """
        if not filename:
            timestamp = datetime.now().strftime(EXPORT_DATE_FORMAT)
            filename = f"phien_{timestamp}.txt"
        
        filepath = EXPORT_DIR / filename
        sessions = SessionRepository.get_all()
        total = sum(s.amount for s in sessions)
        
        content = self._generate_text_report(sessions, total, "Phiên hiện tại")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def export_history_to_text(self, history_id: int, filename: str = None) -> Optional[str]:
        """
        Xuất lịch sử phiên ra file text.
        Trả về đường dẫn file hoặc None nếu không tìm thấy.
        """
        history = HistoryRepository.get_by_id(history_id)
        if not history:
            return None
        
        if not filename:
            timestamp = datetime.now().strftime(EXPORT_DATE_FORMAT)
            filename = f"lichsu_{history_id}_{timestamp}.txt"
        
        filepath = EXPORT_DIR / filename
        
        content = self._generate_history_text_report(history)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def _generate_text_report(self, sessions: List[SessionData], total: float, title: str) -> str:
        """Generate nội dung báo cáo text"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"  {title.upper()}")
        lines.append(f"  Ngày: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"{'STT':<5} {'Sản phẩm':<20} {'Giao':<10} {'Chốt':<10} {'Dùng':<8} {'Tiền':>12}")
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
        lines.append(f"{'STT':<5} {'Sản phẩm':<20} {'Giao':<10} {'Chốt':<10} {'Dùng':<8} {'Tiền':>12}")
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
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Xuất phiên hiện tại ra file CSV.
        """
        if not filename:
            timestamp = datetime.now().strftime(EXPORT_DATE_FORMAT)
            filename = f"phien_{timestamp}.csv"
        
        filepath = EXPORT_DIR / filename
        sessions = SessionRepository.get_all()
        
        lines = ["STT,Sản phẩm,Đơn vị,Quy đổi,Đơn giá,Giao ca,Chốt ca,Đã dùng,Thành tiền"]
        
        for i, s in enumerate(sessions, 1):
            lines.append(
                f"{i},{s.product.name},{s.product.large_unit},{s.product.conversion},"
                f"{s.product.unit_price},{s.handover_qty},{s.closing_qty},"
                f"{s.used_qty},{s.amount}"
            )
        
        total = sum(s.amount for s in sessions)
        lines.append(f",,,,,,,,{total}")
        
        with open(filepath, 'w', encoding='utf-8-sig') as f:
            f.write("\n".join(lines))
        
        return str(filepath)
