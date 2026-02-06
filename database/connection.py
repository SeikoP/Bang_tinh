"""
Database connection management với context manager
"""

import sqlite3
from contextlib import contextmanager
from typing import Generator
import sys
import os

# Thêm parent directory vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager để quản lý database connection.
    Tự động đóng connection khi hoàn thành.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Cho phép truy cập column bằng tên
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """
    Khởi tạo database schema.
    Tạo các bảng nếu chưa tồn tại.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # Bảng products
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                large_unit TEXT NOT NULL,
                conversion INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Bảng session_data (dữ liệu phiên hiện tại)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_data (
                product_id INTEGER PRIMARY KEY,
                handover_qty INTEGER DEFAULT 0,
                closing_qty INTEGER DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """
        )

        # Bảng session_history (lịch sử các phiên)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date DATE NOT NULL,
                shift_name TEXT,
                total_amount REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Bảng session_history_items (chi tiết từng phiên)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS session_history_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                history_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                large_unit TEXT NOT NULL,
                conversion INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                handover_qty INTEGER DEFAULT 0,
                closing_qty INTEGER DEFAULT 0,
                used_qty INTEGER DEFAULT 0,
                amount REAL DEFAULT 0,
                FOREIGN KEY (history_id) REFERENCES session_history (id) ON DELETE CASCADE
            )
        """
        )

        # Migration: thêm cột mới nếu chưa có
        try:
            cursor.execute(
                "ALTER TABLE products ADD COLUMN is_active INTEGER DEFAULT 1"
            )
        except sqlite3.OperationalError:
            pass  # Column đã tồn tại

        try:
            cursor.execute(
                "ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                "ALTER TABLE products ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        except sqlite3.OperationalError:
            pass

        # Bảng quick_prices cho Bảng giá nhanh (nhập tay)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quick_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        try:
            cursor.execute(
                "ALTER TABLE products ADD COLUMN is_favorite INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass

        # Bảng bank_history (lưu lịch sử thông báo ngân hàng)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bank_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_str TEXT,
                source TEXT,
                amount TEXT,
                content TEXT,
                sender_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Migration: Add sender_name column if not exists
        cursor.execute("PRAGMA table_info(bank_history)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'sender_name' not in columns:
            cursor.execute("ALTER TABLE bank_history ADD COLUMN sender_name TEXT")

        # Bảng stock_change_logs (lịch sử thay đổi số lượng kho)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stock_change_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                old_qty INTEGER NOT NULL,
                new_qty INTEGER NOT NULL,
                change_type TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
            )
        """
        )

        # Sample data removed for production build
        # Database will start empty
        # Users can add their own products
        pass
