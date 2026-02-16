"""
Unit tests for CalculatorService
Test các logic tính toán trong tab Tính tiền
"""

import pytest

from core.exceptions import ValidationError
from services.calculator import CalculatorService


class TestCalculatorService:
    """Test suite for CalculatorService"""

    def setup_method(self):
        """Setup test fixtures"""
        self.calc = CalculatorService()

    # ===== Test parse_to_small_units =====

    def test_parse_simple_large_unit(self):
        """Test: '3' với conversion=24 -> 72"""
        result = self.calc.parse_to_small_units("3", 24)
        assert result == 72

    def test_parse_with_dot_notation(self):
        """Test: '3.4' với conversion=24 -> 76"""
        result = self.calc.parse_to_small_units("3.4", 24)
        assert result == 76

    def test_parse_with_letter_notation(self):
        """Test: '3t4' với conversion=24 -> 76"""
        result = self.calc.parse_to_small_units("3t4", 24)
        assert result == 76

    def test_parse_auto_normalize(self):
        """Test: '4.21' với conversion=20 -> 101 (auto normalize to 5.1)"""
        result = self.calc.parse_to_small_units("4.21", 20)
        assert result == 101  # 5*20 + 1

    def test_parse_auto_normalize_exact(self):
        """Test: '4.20' với conversion=20 -> 100 (auto normalize to 5.0)"""
        result = self.calc.parse_to_small_units("4.20", 20)
        assert result == 100  # 5*20 + 0

    def test_parse_auto_normalize_large(self):
        """Test: '2.50' với conversion=24 -> 98 (auto normalize to 4.2)"""
        result = self.calc.parse_to_small_units("2.50", 24)
        assert result == 98  # 4*24 + 2

    def test_parse_only_small_units(self):
        """Test: '.5' với conversion=24 -> 5"""
        result = self.calc.parse_to_small_units(".5", 24)
        assert result == 5

    def test_parse_only_small_units_large(self):
        """Test: '.30' với conversion=24 -> 6 (auto normalize to 1.6)"""
        result = self.calc.parse_to_small_units(".30", 24)
        assert result == 30  # Should be 30, not normalized

    def test_parse_zero(self):
        """Test: '0' -> 0"""
        result = self.calc.parse_to_small_units("0", 24)
        assert result == 0

    def test_parse_zero_dot_zero(self):
        """Test: '0.0' -> 0"""
        result = self.calc.parse_to_small_units("0.0", 24)
        assert result == 0

    def test_parse_empty_string(self):
        """Test: '' -> 0"""
        result = self.calc.parse_to_small_units("", 24)
        assert result == 0

    def test_parse_whitespace(self):
        """Test: '  3t4  ' -> 76 (trim whitespace)"""
        result = self.calc.parse_to_small_units("  3t4  ", 24)
        assert result == 76

    def test_parse_invalid_conversion(self):
        """Test: conversion <= 0 raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.parse_to_small_units("3", 0)

        with pytest.raises(ValidationError):
            self.calc.parse_to_small_units("3", -1)

    def test_parse_various_letter_separators(self):
        """Test: Các ký tự chữ khác nhau đều được chuyển thành dấu chấm"""
        assert self.calc.parse_to_small_units("3t4", 24) == 76
        assert self.calc.parse_to_small_units("3h4", 24) == 76
        assert self.calc.parse_to_small_units("3x4", 24) == 76
        assert self.calc.parse_to_small_units("3T4", 24) == 76  # uppercase

    def test_parse_multiple_letters(self):
        """Test: '3thung4' -> '3.4' -> 76"""
        result = self.calc.parse_to_small_units("3thung4", 24)
        assert result == 76

    def test_parse_only_letters(self):
        """Test: 'abc' -> 0 (invalid input)"""
        result = self.calc.parse_to_small_units("abc", 24)
        assert result == 0

    def test_parse_decimal_conversion(self):
        """Test: Conversion với số lẻ"""
        result = self.calc.parse_to_small_units("2.5", 12)
        assert result == 29  # 2*12 + 5

    def test_parse_large_conversion(self):
        """Test: Conversion lớn (100)"""
        result = self.calc.parse_to_small_units("5.50", 100)
        assert result == 550  # 5*100 + 50

    # ===== Test format_to_display =====

    def test_format_with_remainder(self):
        """Test: 76, 24, 't' -> '3t4'"""
        result = self.calc.format_to_display(76, 24, "t")
        assert result == "3t4"

    def test_format_no_remainder(self):
        """Test: 72, 24, 't' -> '3t'"""
        result = self.calc.format_to_display(72, 24, "t")
        assert result == "3t"

    def test_format_zero(self):
        """Test: 0, 24, 't' -> '0'"""
        result = self.calc.format_to_display(0, 24, "t")
        assert result == "0"

    def test_format_only_small(self):
        """Test: 5, 24, 't' -> '0t5'"""
        result = self.calc.format_to_display(5, 24, "t")
        assert result == "0t5"

    def test_format_negative(self):
        """Test: -10, 24, 't' -> '0'"""
        result = self.calc.format_to_display(-10, 24, "t")
        assert result == "0"

    def test_format_invalid_conversion(self):
        """Test: conversion <= 0 raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.format_to_display(76, 0, "t")

    def test_format_different_units(self):
        """Test: Different unit characters"""
        assert self.calc.format_to_display(76, 24, "h") == "3h4"
        assert self.calc.format_to_display(76, 24, "x") == "3x4"
        assert self.calc.format_to_display(72, 24, "T") == "3T"

    def test_format_large_numbers(self):
        """Test: Large numbers"""
        result = self.calc.format_to_display(2450, 24, "t")
        assert result == "102t2"  # 2450 / 24 = 102 remainder 2

    # ===== Test calculate_used =====

    def test_calculate_used_normal(self):
        """Test: handover=100, closing=30 -> used=70"""
        result = self.calc.calculate_used(100, 30)
        assert result == 70

    def test_calculate_used_no_usage(self):
        """Test: handover=100, closing=100 -> used=0"""
        result = self.calc.calculate_used(100, 100)
        assert result == 0

    def test_calculate_used_all_used(self):
        """Test: handover=100, closing=0 -> used=100"""
        result = self.calc.calculate_used(100, 0)
        assert result == 100

    def test_calculate_used_negative_handover(self):
        """Test: handover < 0 raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.calculate_used(-10, 5)

    def test_calculate_used_negative_closing(self):
        """Test: closing < 0 raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.calculate_used(100, -5)

    def test_calculate_used_closing_exceeds_handover(self):
        """Test: closing > handover raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.calculate_used(50, 100)

    def test_calculate_used_both_zero(self):
        """Test: handover=0, closing=0 -> used=0"""
        result = self.calc.calculate_used(0, 0)
        assert result == 0

    # ===== Test calculate_amount =====

    def test_calculate_amount_normal(self):
        """Test: used=10, price=5000 -> amount=50000"""
        result = self.calc.calculate_amount(10, 5000)
        assert result == 50000

    def test_calculate_amount_zero_used(self):
        """Test: used=0, price=5000 -> amount=0"""
        result = self.calc.calculate_amount(0, 5000)
        assert result == 0

    def test_calculate_amount_zero_price(self):
        """Test: used=10, price=0 -> amount=0"""
        result = self.calc.calculate_amount(10, 0)
        assert result == 0

    def test_calculate_amount_negative_used(self):
        """Test: used < 0 raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.calculate_amount(-10, 5000)

    def test_calculate_amount_negative_price(self):
        """Test: price < 0 raises ValidationError"""
        with pytest.raises(ValidationError):
            self.calc.calculate_amount(10, -5000)

    def test_calculate_amount_decimal_price(self):
        """Test: Decimal price"""
        result = self.calc.calculate_amount(10, 5500.50)
        assert result == 55005.0

    def test_calculate_amount_large_numbers(self):
        """Test: Large numbers"""
        result = self.calc.calculate_amount(1000, 10000)
        assert result == 10000000

    # ===== Test validate_closing_qty =====

    def test_validate_closing_valid(self):
        """Test: Valid closing quantity"""
        is_valid, msg = self.calc.validate_closing_qty(100, 50)
        assert is_valid is True
        assert msg == ""

    def test_validate_closing_equal(self):
        """Test: Closing equals handover"""
        is_valid, msg = self.calc.validate_closing_qty(100, 100)
        assert is_valid is True
        assert msg == ""

    def test_validate_closing_zero(self):
        """Test: Closing is zero"""
        is_valid, msg = self.calc.validate_closing_qty(100, 0)
        assert is_valid is True
        assert msg == ""

    def test_validate_closing_negative(self):
        """Test: Negative closing quantity"""
        is_valid, msg = self.calc.validate_closing_qty(100, -5)
        assert is_valid is False
        assert "âm" in msg.lower()

    def test_validate_closing_exceeds_handover(self):
        """Test: Closing exceeds handover"""
        is_valid, msg = self.calc.validate_closing_qty(50, 100)
        assert is_valid is False
        assert "lớn hơn" in msg.lower()

    def test_validate_closing_both_zero(self):
        """Test: Both zero"""
        is_valid, msg = self.calc.validate_closing_qty(0, 0)
        assert is_valid is True
        assert msg == ""

    # ===== Test normalize_input =====

    def test_normalize_input(self):
        """Test: normalize_input is alias for parse_to_small_units"""
        result = self.calc.normalize_input("3t4", 24)
        assert result == 76

    # ===== Integration Tests =====

    def test_full_calculation_flow(self):
        """Test: Full flow từ input -> calculation -> display"""
        # Parse input
        handover = self.calc.parse_to_small_units("5t10", 24)  # 5*24 + 10 = 130
        closing = self.calc.parse_to_small_units("2t5", 24)  # 2*24 + 5 = 53

        # Calculate used
        used = self.calc.calculate_used(handover, closing)
        assert used == 77  # 130 - 53

        # Calculate amount
        amount = self.calc.calculate_amount(used, 5000)
        assert amount == 385000  # 77 * 5000

        # Format display
        display = self.calc.format_to_display(closing, 24, "t")
        assert display == "2t5"

    def test_full_flow_beer_case(self):
        """Test: Real case - Bia thùng 24 lon"""
        # Giao ca: 10 thùng
        handover = self.calc.parse_to_small_units("10", 24)
        assert handover == 240

        # Chốt ca: 3 thùng 5 lon
        closing = self.calc.parse_to_small_units("3t5", 24)
        assert closing == 77

        # Đã dùng
        used = self.calc.calculate_used(handover, closing)
        assert used == 163  # 240 - 77

        # Thành tiền (5000đ/lon)
        amount = self.calc.calculate_amount(used, 5000)
        assert amount == 815000

    def test_full_flow_water_case(self):
        """Test: Real case - Nước suối thùng 20 chai"""
        # Giao ca: 5.10 (5 thùng 10 chai)
        handover = self.calc.parse_to_small_units("5.10", 20)
        assert handover == 110

        # Chốt ca: 2.5
        closing = self.calc.parse_to_small_units("2.5", 20)
        assert closing == 45

        # Đã dùng
        used = self.calc.calculate_used(handover, closing)
        assert used == 65

        # Thành tiền (3000đ/chai)
        amount = self.calc.calculate_amount(used, 3000)
        assert amount == 195000

    def test_edge_case_large_numbers(self):
        """Test: Large numbers"""
        result = self.calc.parse_to_small_units("100t50", 24)
        assert result == 2450  # 100*24 + 50

        amount = self.calc.calculate_amount(2450, 10000)
        assert amount == 24500000

    def test_edge_case_conversion_1(self):
        """Test: Conversion = 1 (no conversion)"""
        result = self.calc.parse_to_small_units("5", 1)
        assert result == 5

        display = self.calc.format_to_display(5, 1, "x")
        assert display == "5x"

    def test_edge_case_single_unit_product(self):
        """Test: Sản phẩm bán lẻ (conversion=1)"""
        handover = self.calc.parse_to_small_units("50", 1)
        closing = self.calc.parse_to_small_units("20", 1)
        used = self.calc.calculate_used(handover, closing)
        assert used == 30

    def test_roundtrip_parse_format(self):
        """Test: Parse -> Format should be consistent"""
        original = "5t10"
        parsed = self.calc.parse_to_small_units(original, 24)
        formatted = self.calc.format_to_display(parsed, 24, "t")
        assert formatted == original

    def test_roundtrip_various_inputs(self):
        """Test: Various roundtrip conversions"""
        test_cases = [
            ("3t4", 24, "3t4"),
            ("10t", 24, "10t"),
            ("0t5", 24, "0t5"),
            ("1t0", 24, "1t"),
        ]

        for input_str, conv, expected in test_cases:
            parsed = self.calc.parse_to_small_units(input_str, conv)
            formatted = self.calc.format_to_display(parsed, conv, "t")
            assert formatted == expected, f"Failed for {input_str}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
