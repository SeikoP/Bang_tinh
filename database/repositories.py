"""
Repositories - CRUD operations cho database
Implements core interfaces with proper error handling and transaction management
"""
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .connection import get_connection
from core.models import Product, SessionData, SessionHistory, SessionHistoryItem, QuickPrice, BankNotification, StockChangeLog
from core.interfaces import IProductRepository, ISessionRepository, IHistoryRepository
from core.exceptions import DatabaseError, ValidationError


class ProductRepository(IProductRepository):
    """Repository cho quản lý sản phẩm"""
    
    @staticmethod
    def get_all(include_inactive: bool = False) -> List[Product]:
        """Lấy tất cả sản phẩm"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                if include_inactive:
                    cursor.execute("SELECT * FROM products ORDER BY name")
                else:
                    cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY name")
                return [Product.from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Failed to get products: {str(e)}", "get_all")
    
    @staticmethod
    def get_by_id(product_id: int) -> Optional[Product]:
        """Lấy sản phẩm theo ID"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
                row = cursor.fetchone()
                return Product.from_row(row) if row else None
        except Exception as e:
            raise DatabaseError(f"Failed to get product by ID: {str(e)}", "get_by_id")
    
    @staticmethod
    def search(keyword: str) -> List[Product]:
        """Tìm kiếm sản phẩm theo tên"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM products WHERE is_active = 1 AND name LIKE ? ORDER BY name",
                    (f"%{keyword}%",)
                )
                return [Product.from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Failed to search products: {str(e)}", "search")
    
    @staticmethod
    def add(name: str, large_unit: str, conversion: int, unit_price: float) -> int:
        """Thêm sản phẩm mới, trả về ID"""
        try:
            # Validate inputs
            if not name or len(name.strip()) == 0:
                raise ValidationError("Product name cannot be empty", "name")
            if conversion <= 0:
                raise ValidationError("Conversion must be positive", "conversion")
            if unit_price < 0:
                raise ValidationError("Unit price cannot be negative", "unit_price")
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Transaction: Insert product and create session_data
                cursor.execute(
                    """INSERT INTO products (name, large_unit, conversion, unit_price) 
                       VALUES (?, ?, ?, ?)""",
                    (name, large_unit, conversion, unit_price)
                )
                product_id = cursor.lastrowid
                
                # Tạo session_data cho sản phẩm mới
                cursor.execute(
                    "INSERT INTO session_data (product_id) VALUES (?)",
                    (product_id,)
                )
                
                return product_id
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to add product: {str(e)}", "add")
    
    @staticmethod
    def update(product_id: int, name: str, large_unit: str, 
               conversion: int, unit_price: float) -> bool:
        """Cập nhật sản phẩm"""
        try:
            # Validate inputs
            if not name or len(name.strip()) == 0:
                raise ValidationError("Product name cannot be empty", "name")
            if conversion <= 0:
                raise ValidationError("Conversion must be positive", "conversion")
            if unit_price < 0:
                raise ValidationError("Unit price cannot be negative", "unit_price")
            
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE products 
                       SET name=?, large_unit=?, conversion=?, unit_price=?
                       WHERE id=?""",
                    (name, large_unit, conversion, unit_price, product_id)
                )
                return cursor.rowcount > 0
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update product: {str(e)}", "update")
    
    @staticmethod
    def delete(product_id: int, soft_delete: bool = True) -> bool:
        """Xóa sản phẩm (mặc định soft delete)"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Transaction: Delete product and related session_data
                if soft_delete:
                    cursor.execute(
                        "UPDATE products SET is_active = 0 WHERE id=?",
                        (product_id,)
                    )
                else:
                    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
                    cursor.execute("DELETE FROM session_data WHERE product_id=?", (product_id,))
                
                return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete product: {str(e)}", "delete")

    @staticmethod
    def toggle_favorite(product_id: int) -> bool:
        """Bật/tắt trạng thái yêu thích"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE products SET is_favorite = NOT is_favorite WHERE id = ?", (product_id,))
                return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to toggle favorite: {str(e)}", "toggle_favorite")


class SessionRepository(ISessionRepository):
    """Repository cho quản lý session data (phiên làm việc hiện tại)"""
    
    @staticmethod
    def get_all() -> List[SessionData]:
        """Lấy dữ liệu phiên hiện tại cho tất cả sản phẩm active"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT p.id, p.name, p.large_unit, p.conversion, p.unit_price, p.is_active, p.is_favorite,
                           COALESCE(s.handover_qty, 0) as handover_qty, 
                           COALESCE(s.closing_qty, 0) as closing_qty
                    FROM products p
                    LEFT JOIN session_data s ON p.id = s.product_id
                    WHERE p.is_active = 1
                    ORDER BY p.name
                ''')
                return [SessionData.from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Failed to get session data: {str(e)}", "get_all")
    
    @staticmethod
    def update_qty(product_id: int, handover: int, closing: int) -> bool:
        """Cập nhật số lượng giao ca/chốt ca"""
        try:
            # Validate quantities
            if handover < 0:
                raise ValidationError("Handover quantity cannot be negative", "handover")
            if closing < 0:
                raise ValidationError("Closing quantity cannot be negative", "closing")
            
            # Đảm bảo chốt ca không lớn hơn giao ca
            if closing > handover:
                closing = handover
                
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT OR REPLACE INTO session_data (product_id, handover_qty, closing_qty)
                       VALUES (?, ?, ?)""",
                    (product_id, handover, closing)
                )
                return cursor.rowcount > 0
        except ValidationError:
            raise
        except Exception as e:
            raise DatabaseError(f"Failed to update quantities: {str(e)}", "update_qty")
    
    @staticmethod
    def reset_all() -> bool:
        """Reset tất cả số lượng về 0"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE session_data SET handover_qty = 0, closing_qty = 0")
                return True
        except Exception as e:
            raise DatabaseError(f"Failed to reset session data: {str(e)}", "reset_all")
    
    @staticmethod
    def get_total_amount() -> float:
        """Tính tổng tiền của phiên hiện tại"""
        try:
            sessions = SessionRepository.get_all()
            return float(sum(s.amount for s in sessions))
        except Exception as e:
            raise DatabaseError(f"Failed to calculate total amount: {str(e)}", "get_total_amount")


class HistoryRepository(IHistoryRepository):
    """Repository cho quản lý lịch sử phiên"""
    
    @staticmethod
    def save_current_session(shift_name: str = None, notes: str = None) -> int:
        """Lưu phiên hiện tại vào lịch sử"""
        try:
            sessions = SessionRepository.get_all()
            total = sum(s.amount for s in sessions)
            
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Transaction: Create session history and save items
                cursor.execute(
                    """INSERT INTO session_history (session_date, shift_name, total_amount, notes)
                       VALUES (?, ?, ?, ?)""",
                    (date.today().isoformat(), shift_name, float(total), notes)
                )
                history_id = cursor.lastrowid
                
                # Lưu chi tiết từng sản phẩm
                for s in sessions:
                    cursor.execute(
                        """INSERT INTO session_history_items 
                           (history_id, product_id, product_name, large_unit, conversion, 
                            unit_price, handover_qty, closing_qty, used_qty, amount)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (history_id, s.product.id, s.product.name, s.product.large_unit,
                         s.product.conversion, float(s.product.unit_price), s.handover_qty,
                         s.closing_qty, s.used_qty, float(s.amount))
                    )
                
                return history_id
        except Exception as e:
            raise DatabaseError(f"Failed to save session: {str(e)}", "save_current_session")
    
    @staticmethod
    def get_all(limit: int = 50) -> List[SessionHistory]:
        """Lấy danh sách lịch sử phiên"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM session_history 
                       ORDER BY created_at DESC LIMIT ?""",
                    (limit,)
                )
                return [SessionHistory.from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Failed to get session history: {str(e)}", "get_all")
    
    @staticmethod
    def get_by_id(history_id: int) -> Optional[SessionHistory]:
        """Lấy chi tiết một phiên lịch sử"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM session_history WHERE id = ?", (history_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                
                history = SessionHistory.from_row(row)
                
                # Lấy chi tiết items
                cursor.execute(
                    "SELECT * FROM session_history_items WHERE history_id = ?",
                    (history_id,)
                )
                history.items = [SessionHistoryItem.from_row(r) for r in cursor.fetchall()]
                
                return history
        except Exception as e:
            raise DatabaseError(f"Failed to get session history by ID: {str(e)}", "get_by_id")
    
    @staticmethod
    def get_by_date_range(start_date: date, end_date: date) -> List[SessionHistory]:
        """Lấy lịch sử theo khoảng thời gian"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM session_history 
                       WHERE session_date BETWEEN ? AND ?
                       ORDER BY created_at DESC""",
                    (start_date.isoformat(), end_date.isoformat())
                )
                return [SessionHistory.from_row(row) for row in cursor.fetchall()]
        except Exception as e:
            raise DatabaseError(f"Failed to get session history by date range: {str(e)}", "get_by_date_range")
    
    @staticmethod
    def delete(history_id: int) -> bool:
        """Xóa một phiên lịch sử"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                
                # Transaction: Delete items first, then history
                cursor.execute("DELETE FROM session_history_items WHERE history_id = ?", (history_id,))
                cursor.execute("DELETE FROM session_history WHERE id = ?", (history_id,))
                
                return cursor.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete session history: {str(e)}", "delete")


class QuickPriceRepository:
    """Repository cho Bảng giá nhanh (nhập tay)"""
    
    @staticmethod
    def get_all() -> List[QuickPrice]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM quick_prices ORDER BY id")
            return [QuickPrice.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def add(name: str, price: float) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO quick_prices (name, price) VALUES (?, ?)",
                (name, price)
            )
            return cursor.lastrowid
            
    @staticmethod
    def update(id: int, name: str, price: float) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE quick_prices SET name=?, price=? WHERE id=?",
                (name, price, id)
            )
            return cursor.rowcount > 0
            
    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM quick_prices WHERE id=?", (id,))
            return cursor.rowcount > 0


class BankRepository:
    """Repository cho lịch sử thông báo ngân hàng"""
    
    @staticmethod
    def add(time_str: str, source: str, amount: str, content: str) -> int:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO bank_history (time_str, source, amount, content) 
                   VALUES (?, ?, ?, ?)""",
                (time_str, source, amount, content)
            )
            return cursor.lastrowid

    @staticmethod
    def get_all(limit: int = 100) -> List[BankNotification]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bank_history ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [BankNotification.from_row(row) for row in cursor.fetchall()]

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bank_history WHERE id=?", (id,))
            return cursor.rowcount > 0

    @staticmethod
    def clear_all() -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bank_history")
            return True


class StockChangeLogRepository:
    """Repository cho lịch sử thay đổi kho"""
    
    @staticmethod
    def add_log(product_id: int, product_name: str, old_qty: int, new_qty: int):
        """Thêm log thay đổi số lượng"""
        change_type = 'increase' if new_qty > old_qty else 'decrease'
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO stock_change_logs 
                (product_id, product_name, old_qty, new_qty, change_type) 
                VALUES (?, ?, ?, ?, ?)""",
                (product_id, product_name, old_qty, new_qty, change_type)
            )
            return cursor.lastrowid
    
    @staticmethod
    def get_all(limit: int = 100) -> List[StockChangeLog]:
        """Lấy lịch sử thay đổi, mới nhất trước"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM stock_change_logs 
                ORDER BY changed_at DESC LIMIT ?""",
                (limit,)
            )
            return [StockChangeLog.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete(log_id: int) -> bool:
        """Xóa một log cụ thể"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock_change_logs WHERE id = ?", (log_id,))
            return cursor.rowcount > 0
    
    @staticmethod
    def clear_all():
        """Xóa toàn bộ lịch sử"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stock_change_logs")
