"""
Unit tests cho utils/formatters.py
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.formatters import parse_to_small_units, format_to_display, format_currency


class TestFormatters(unittest.TestCase):
    """Test cases cho formatters"""
    
    def test_parse_simple_number(self):
        """Test parse số đơn giản"""
        # 3 thùng = 3 * 24 = 72 đơn vị nhỏ
        self.assertEqual(parse_to_small_units("3", 24), 72)
        self.assertEqual(parse_to_small_units("5", 30), 150)
    
    def test_parse_with_dot(self):
        """Test parse với dấu chấm: 3.4 = 3 thùng + 4 đơn vị"""
        self.assertEqual(parse_to_small_units("3.4", 24), 76)  # 3*24 + 4
        self.assertEqual(parse_to_small_units("2.15", 30), 75)  # 2*30 + 15
    
    def test_parse_with_unit_char(self):
        """Test parse với ký tự đơn vị: 3t4"""
        self.assertEqual(parse_to_small_units("3t4", 24), 76)
        self.assertEqual(parse_to_small_units("2v15", 30), 75)
        self.assertEqual(parse_to_small_units("10k5", 20), 205)  # 10*20 + 5
    
    def test_parse_empty_and_invalid(self):
        """Test parse chuỗi rỗng và không hợp lệ"""
        self.assertEqual(parse_to_small_units("", 24), 0)
        self.assertEqual(parse_to_small_units(None, 24), 0)
        self.assertEqual(parse_to_small_units("abc", 24), 0)
    
    def test_parse_only_small_units(self):
        """Test parse chỉ có đơn vị nhỏ"""
        self.assertEqual(parse_to_small_units("0.5", 24), 5)
        self.assertEqual(parse_to_small_units(".10", 30), 10)
    
    def test_format_to_display_normal(self):
        """Test format hiển thị bình thường"""
        self.assertEqual(format_to_display(76, 24, "t"), "3t4")
        self.assertEqual(format_to_display(75, 30, "v"), "2v15")
    
    def test_format_to_display_exact(self):
        """Test format khi chia hết"""
        self.assertEqual(format_to_display(72, 24, "t"), "3t")
        self.assertEqual(format_to_display(60, 30, "v"), "2v")
    
    def test_format_to_display_zero(self):
        """Test format số 0"""
        self.assertEqual(format_to_display(0, 24, "t"), "0t")
    
    def test_format_to_display_negative(self):
        """Test format số âm -> trả về 0"""
        self.assertEqual(format_to_display(-10, 24, "t"), "0")
    
    def test_format_currency(self):
        """Test format tiền tệ"""
        self.assertEqual(format_currency(1000000), "1,000,000 đ")
        self.assertEqual(format_currency(50000), "50,000 đ")
        self.assertEqual(format_currency(0), "0 đ")


class TestEdgeCases(unittest.TestCase):
    """Test các trường hợp biên"""
    
    def test_large_numbers(self):
        """Test với số lớn"""
        result = parse_to_small_units("100.50", 24)
        self.assertEqual(result, 2450)  # 100*24 + 50
        
        self.assertEqual(format_to_display(2450, 24, "t"), "102t2")
    
    def test_conversion_factor_1(self):
        """Test với hệ số quy đổi = 1"""
        self.assertEqual(parse_to_small_units("5", 1), 5)
        self.assertEqual(format_to_display(5, 1, "u"), "5u")


if __name__ == "__main__":
    unittest.main()
