"""
Repositories - CRUD operations cho database
"""
from typing import List, Optional
from datetime import date, datetime
from .connection import get_connection
from .models import Product, SessionData, SessionHistory, SessionHistoryItem, QuickPrice, BankNotification


class ProductRepository:
    """Repository cho quản lý sản phẩm"""
    
    @staticmethod
    def get_all(include_inactive: bool = False) -> List[Product]:
        """Lấy tất cả sản phẩm"""
        with get_connection() as conn:
            cursor = conn.cursor()
            if include_inactive:
                cursor.execute("SELECT * FROM products ORDER BY name")
            else:
                cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY name")
            return [Product.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_by_id(product_id: int) -> Optional[Product]:
        """Lấy sản phẩm theo ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()
            return Product.from_row(row) if row else None
    
    @staticmethod
    def search(keyword: str) -> List[Product]:
        """Tìm kiếm sản phẩm theo tên"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM products WHERE is_active = 1 AND name LIKE ? ORDER BY name",
                (f"%{keyword}%",)
            )
            return [Product.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def add(name: str, large_unit: str, conversion: int, unit_price: float) -> int:
        """Thêm sản phẩm mới, trả về ID"""
        with get_connection() as conn:
            cursor = conn.cursor()
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
    
    @staticmethod
    def update(product_id: int, name: str, large_unit: str, 
               conversion: int, unit_price: float) -> bool:
        """Cập nhật sản phẩm"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE products 
                   SET name=?, large_unit=?, conversion=?, unit_price=?
                   WHERE id=?""",
                (name, large_unit, conversion, unit_price, product_id)
            )
            return cursor.rowcount > 0
    
    @staticmethod
    def delete(product_id: int, soft_delete: bool = True) -> bool:
        """Xóa sản phẩm (mặc định soft delete)"""
        with get_connection() as conn:
            cursor = conn.cursor()
            if soft_delete:
                cursor.execute(
                    "UPDATE products SET is_active = 0 WHERE id=?",
                    (product_id,)
                )
            else:
                cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
                cursor.execute("DELETE FROM session_data WHERE product_id=?", (product_id,))
            return cursor.rowcount > 0

    @staticmethod
    def toggle_favorite(product_id: int) -> bool:
        """Bật/tắt trạng thái yêu thích"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET is_favorite = NOT is_favorite WHERE id = ?", (product_id,))
            return cursor.rowcount > 0


class SessionRepository:
    """Repository cho quản lý session data (phiên làm việc hiện tại)"""
    
    @staticmethod
    def get_all() -> List[SessionData]:
        """Lấy dữ liệu phiên hiện tại cho tất cả sản phẩm active"""
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
    
    @staticmethod
    def update_qty(product_id: int, handover: int, closing: int) -> bool:
        """Cập nhật số lượng giao ca/chốt ca"""
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
    
    @staticmethod
    def reset_all() -> bool:
        """Reset tất cả số lượng về 0"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE session_data SET handover_qty = 0, closing_qty = 0")
            return True
    
    @staticmethod
    def get_total_amount() -> float:
        """Tính tổng tiền của phiên hiện tại"""
        sessions = SessionRepository.get_all()
        return sum(s.amount for s in sessions)


class HistoryRepository:
    """Repository cho quản lý lịch sử phiên"""
    
    @staticmethod
    def save_current_session(shift_name: str = None, notes: str = None) -> int:
        """Lưu phiên hiện tại vào lịch sử"""
        sessions = SessionRepository.get_all()
        total = sum(s.amount for s in sessions)
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Tạo session history
            cursor.execute(
                """INSERT INTO session_history (session_date, shift_name, total_amount, notes)
                   VALUES (?, ?, ?, ?)""",
                (date.today().isoformat(), shift_name, total, notes)
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
                     s.product.conversion, s.product.unit_price, s.handover_qty,
                     s.closing_qty, s.used_qty, s.amount)
                )
            
            return history_id
    
    @staticmethod
    def get_all(limit: int = 50) -> List[SessionHistory]:
        """Lấy danh sách lịch sử phiên"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM session_history 
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            )
            return [SessionHistory.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_by_id(history_id: int) -> Optional[SessionHistory]:
        """Lấy chi tiết một phiên lịch sử"""
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
    
    @staticmethod
    def get_by_date_range(start_date: date, end_date: date) -> List[SessionHistory]:
        """Lấy lịch sử theo khoảng thời gian"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM session_history 
                   WHERE session_date BETWEEN ? AND ?
                   ORDER BY created_at DESC""",
                (start_date.isoformat(), end_date.isoformat())
            )
            return [SessionHistory.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete(history_id: int) -> bool:
        """Xóa một phiên lịch sử"""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM session_history_items WHERE history_id = ?", (history_id,))
            cursor.execute("DELETE FROM session_history WHERE id = ?", (history_id,))
            return cursor.rowcount > 0


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
