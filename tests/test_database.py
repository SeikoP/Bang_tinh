"""
Unit tests cho database repositories
"""
import unittest
import sys
import os
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use test database
import config
config.DB_PATH = Path(__file__).parent / "test_storage.db"

from database.connection import init_db, get_connection
from database.repositories import ProductRepository, SessionRepository


class TestProductRepository(unittest.TestCase):
    """Test cases cho ProductRepository"""
    
    @classmethod
    def setUpClass(cls):
        """Setup test database"""
        # Remove test db if exists
        if config.DB_PATH.exists():
            os.remove(config.DB_PATH)
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup test database"""
        if config.DB_PATH.exists():
            os.remove(config.DB_PATH)
    
    def test_add_product(self):
        """Test thêm sản phẩm"""
        product_id = ProductRepository.add("Test Product", "Thùng", 24, 10000)
        self.assertIsNotNone(product_id)
        self.assertGreater(product_id, 0)
    
    def test_get_all_products(self):
        """Test lấy tất cả sản phẩm"""
        products = ProductRepository.get_all()
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
    
    def test_get_product_by_id(self):
        """Test lấy sản phẩm theo ID"""
        products = ProductRepository.get_all()
        if products:
            product = ProductRepository.get_by_id(products[0].id)
            self.assertIsNotNone(product)
            self.assertEqual(product.id, products[0].id)
    
    def test_update_product(self):
        """Test cập nhật sản phẩm"""
        product_id = ProductRepository.add("To Update", "Vỉ", 30, 5000)
        result = ProductRepository.update(product_id, "Updated Name", "Gói", 10, 6000)
        self.assertTrue(result)
        
        updated = ProductRepository.get_by_id(product_id)
        self.assertEqual(updated.name, "Updated Name")
        self.assertEqual(updated.large_unit, "Gói")
        self.assertEqual(updated.conversion, 10)
        self.assertEqual(updated.unit_price, 6000)
    
    def test_search_product(self):
        """Test tìm kiếm sản phẩm"""
        ProductRepository.add("Apple Juice", "Thùng", 24, 15000)
        ProductRepository.add("Orange Juice", "Thùng", 24, 12000)
        
        results = ProductRepository.search("Juice")
        self.assertGreaterEqual(len(results), 2)
        
        results = ProductRepository.search("Apple")
        self.assertGreaterEqual(len(results), 1)
    
    def test_soft_delete(self):
        """Test soft delete sản phẩm"""
        product_id = ProductRepository.add("To Delete", "Két", 20, 20000)
        result = ProductRepository.delete(product_id, soft_delete=True)
        self.assertTrue(result)
        
        # Should not appear in regular get_all
        products = ProductRepository.get_all()
        deleted = [p for p in products if p.id == product_id]
        self.assertEqual(len(deleted), 0)
        
        # But should appear with include_inactive
        all_products = ProductRepository.get_all(include_inactive=True)
        deleted = [p for p in all_products if p.id == product_id]
        self.assertEqual(len(deleted), 1)


class TestSessionRepository(unittest.TestCase):
    """Test cases cho SessionRepository"""
    
    @classmethod
    def setUpClass(cls):
        """Setup"""
        if not config.DB_PATH.exists():
            init_db()
    
    def test_get_all_session_data(self):
        """Test lấy tất cả session data"""
        sessions = SessionRepository.get_all()
        self.assertIsInstance(sessions, list)
    
    def test_update_qty(self):
        """Test cập nhật số lượng"""
        sessions = SessionRepository.get_all()
        if sessions:
            product_id = sessions[0].product.id
            result = SessionRepository.update_qty(product_id, 100, 50)
            self.assertTrue(result)
            
            # Verify
            updated_sessions = SessionRepository.get_all()
            updated = [s for s in updated_sessions if s.product.id == product_id][0]
            self.assertEqual(updated.handover_qty, 100)
            self.assertEqual(updated.closing_qty, 50)
            self.assertEqual(updated.used_qty, 50)
    
    def test_reset_all(self):
        """Test reset tất cả số lượng"""
        result = SessionRepository.reset_all()
        self.assertTrue(result)
        
        sessions = SessionRepository.get_all()
        for s in sessions:
            self.assertEqual(s.handover_qty, 0)
            self.assertEqual(s.closing_qty, 0)
    
    def test_get_total_amount(self):
        """Test tính tổng tiền"""
        total = SessionRepository.get_total_amount()
        self.assertIsInstance(total, (int, float))
        self.assertGreaterEqual(total, 0)


if __name__ == "__main__":
    unittest.main()
