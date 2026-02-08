"""
Base Repository with SQL Injection Prevention
"""

import sqlite3
from contextlib import contextmanager
from typing import Any, Generator, List, Optional, Tuple

from database.connection import get_connection


class SafeRepository:
    """
    Base repository with SQL injection prevention
    
    Rules:
    1. NEVER use string formatting for SQL
    2. ALWAYS use parameterized queries
    3. ALWAYS validate input types
    4. ALWAYS use context managers
    """
    
    @contextmanager
    def _get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """Get database cursor with automatic commit/rollback"""
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    
    def _execute_safe(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> sqlite3.Cursor:
        """
        Execute query safely with parameterized values
        
        Args:
            query: SQL query with ? placeholders
            params: Tuple of parameters
            
        Returns:
            Cursor with results
            
        Example:
            # GOOD ✓
            self._execute_safe(
                "SELECT * FROM products WHERE name = ?",
                (product_name,)
            )
            
            # BAD ✗
            cursor.execute(f"SELECT * FROM products WHERE name = '{product_name}'")
        """
        with self._get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
    
    def _execute_many_safe(
        self,
        query: str,
        params_list: List[Tuple[Any, ...]]
    ) -> sqlite3.Cursor:
        """Execute many queries safely"""
        with self._get_cursor() as cursor:
            cursor.executemany(query, params_list)
            return cursor
    
    def _fetch_one(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> Optional[sqlite3.Row]:
        """Fetch single row"""
        with self._get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
    
    def _fetch_all(
        self,
        query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[sqlite3.Row]:
        """Fetch all rows"""
        with self._get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def _validate_id(self, id_value: Any) -> int:
        """Validate ID is integer"""
        try:
            return int(id_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid ID: {id_value}")
    
    def _validate_string(self, value: Any, max_length: int = 1000) -> str:
        """Validate string input"""
        if not isinstance(value, str):
            raise ValueError(f"Expected string, got {type(value)}")
        
        if len(value) > max_length:
            raise ValueError(f"String too long: {len(value)} > {max_length}")
        
        return value
    
    def _validate_number(self, value: Any) -> float:
        """Validate numeric input"""
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid number: {value}")


# Example: Refactor existing repository
class ProductRepositorySafe(SafeRepository):
    """Safe product repository"""
    
    def get_by_id(self, product_id: int) -> Optional[sqlite3.Row]:
        """Get product by ID - SQL injection safe"""
        product_id = self._validate_id(product_id)
        
        return self._fetch_one(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
    
    def search_by_name(self, name: str) -> List[sqlite3.Row]:
        """Search products by name - SQL injection safe"""
        name = self._validate_string(name, max_length=200)
        
        return self._fetch_all(
            "SELECT * FROM products WHERE name LIKE ? AND is_active = 1",
            (f'%{name}%',)
        )
    
    def create(
        self,
        name: str,
        large_unit: str,
        conversion: int,
        unit_price: float
    ) -> int:
        """Create product - SQL injection safe"""
        # Validate inputs
        name = self._validate_string(name, max_length=200)
        large_unit = self._validate_string(large_unit, max_length=50)
        conversion = self._validate_id(conversion)
        unit_price = self._validate_number(unit_price)
        
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO products (name, large_unit, conversion, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (name, large_unit, conversion, unit_price)
            )
            return cursor.lastrowid
    
    def update(
        self,
        product_id: int,
        name: str,
        large_unit: str,
        conversion: int,
        unit_price: float
    ):
        """Update product - SQL injection safe"""
        product_id = self._validate_id(product_id)
        name = self._validate_string(name, max_length=200)
        large_unit = self._validate_string(large_unit, max_length=50)
        conversion = self._validate_id(conversion)
        unit_price = self._validate_number(unit_price)
        
        self._execute_safe(
            """
            UPDATE products
            SET name = ?, large_unit = ?, conversion = ?, unit_price = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (name, large_unit, conversion, unit_price, product_id)
        )
    
    def delete(self, product_id: int):
        """Soft delete product - SQL injection safe"""
        product_id = self._validate_id(product_id)
        
        self._execute_safe(
            "UPDATE products SET is_active = 0 WHERE id = ?",
            (product_id,)
        )
