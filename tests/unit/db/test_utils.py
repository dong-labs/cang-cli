"""测试金额转换工具模块

测试 cang.db.utils 模块的所有函数:
- to_cents()
- from_cents()
- from_cents_decimal()
- format_currency()
"""

from decimal import Decimal

import pytest

from cang.db.utils import (
    to_cents,
    from_cents,
    from_cents_decimal,
    format_currency,
)


# =============================================================================
# to_cents() 测试
# =============================================================================

class TestToCents:
    """测试 to_cents 函数"""

    # -------------------------------------------------------------------------
    # 正常路径测试
    # -------------------------------------------------------------------------

    def test_float_input(self):
        """测试 float 类型输入"""
        assert to_cents(29.9) == 2990
        assert to_cents(100.0) == 10000
        assert to_cents(0.01) == 1

    def test_string_input(self):
        """测试字符串类型输入"""
        assert to_cents("29.9") == 2990
        assert to_cents("100") == 10000
        assert to_cents("0.01") == 1

    def test_int_input(self):
        """测试整数类型输入"""
        assert to_cents(100) == 10000
        assert to_cents(0) == 0

    def test_decimal_input(self):
        """测试 Decimal 类型输入"""
        assert to_cents(Decimal("29.9")) == 2990
        assert to_cents(Decimal("100")) == 10000

    # -------------------------------------------------------------------------
    # 边界条件测试
    # -------------------------------------------------------------------------

    def test_zero(self):
        """测试零值"""
        assert to_cents(0) == 0
        assert to_cents(0.0) == 0
        assert to_cents("0") == 0

    def test_negative_values(self):
        """测试负数（支出场景）"""
        assert to_cents(-10.5) == -1050
        assert to_cents("-15.99") == -1599
        assert to_cents(-100) == -10000

    def test_rounding_half_up(self):
        """测试四舍五入"""
        # 向上取整
        assert to_cents(1.005) == 101  # 1.005 -> 1.01
        assert to_cents(2.555) == 256  # 2.555 -> 2.56

        # 向下取整
        assert to_cents(1.004) == 100  # 1.004 -> 1.00
        assert to_cents(2.554) == 255  # 2.554 -> 2.55

    def test_large_values(self):
        """测试大数值"""
        assert to_cents(999999.99) == 99999999
        assert to_cents("1000000") == 100000000

    # -------------------------------------------------------------------------
    # 异常输入测试
    # -------------------------------------------------------------------------

    def test_invalid_string(self):
        """测试无效字符串输入"""
        with pytest.raises(ValueError, match="Invalid amount"):
            to_cents("invalid")

        with pytest.raises(ValueError, match="Invalid amount"):
            to_cents("")

        with pytest.raises(ValueError, match="Invalid amount"):
            to_cents("  ")

    def test_none_input(self):
        """测试 None 输入"""
        with pytest.raises(ValueError, match="Invalid amount"):
            to_cents(None)

    def test_string_with_whitespace(self):
        """测试带空格的字符串（应该被正确处理）"""
        assert to_cents(" 29.9 ") == 2990
        assert to_cents("\t100\n") == 10000


# =============================================================================
# from_cents() 测试
# =============================================================================

class TestFromCents:
    """测试 from_cents 函数"""

    # -------------------------------------------------------------------------
    # 正常路径测试
    # -------------------------------------------------------------------------

    def test_basic_conversion(self):
        """测试基本转换"""
        assert from_cents(2990) == "29.90"
        assert from_cents(10000) == "100.00"
        assert from_cents(100) == "1.00"

    def test_zero(self):
        """测试零值"""
        assert from_cents(0) == "0.00"

    def test_negative_values(self):
        """测试负数"""
        assert from_cents(-1550) == "-15.50"
        assert from_cents(-100) == "-1.00"

    def test_always_two_decimal_places(self):
        """测试始终保留两位小数"""
        assert from_cents(1) == "0.01"
        assert from_cents(10) == "0.10"
        assert from_cents(100) == "1.00"
        assert from_cents(1000) == "10.00"

    def test_formatting(self):
        """测试输出格式（使用 pytest.approx 处理浮点精度）"""
        result = from_cents(2990)
        assert result == "29.90"

        result = from_cents(999999)
        assert result == "9999.99"


# =============================================================================
# from_cents_decimal() 测试
# =============================================================================

class TestFromCentsDecimal:
    """测试 from_cents_decimal 函数"""

    # -------------------------------------------------------------------------
    # 正常路径测试
    # -------------------------------------------------------------------------

    def test_returns_decimal(self):
        """测试返回 Decimal 类型"""
        result = from_cents_decimal(2990)
        assert isinstance(result, Decimal)

    def test_basic_conversion(self):
        """测试基本转换"""
        assert from_cents_decimal(2990) == Decimal("29.90")
        assert from_cents_decimal(10000) == Decimal("100.00")
        assert from_cents_decimal(100) == Decimal("1.00")

    def test_zero(self):
        """测试零值"""
        assert from_cents_decimal(0) == Decimal("0")

    def test_negative_values(self):
        """测试负数"""
        assert from_cents_decimal(-1550) == Decimal("-15.50")
        assert from_cents_decimal(-100) == Decimal("-1.00")

    def test_precision_preserved(self):
        """测试精度保持"""
        # Decimal 保持精确的小数位数
        result = from_cents_decimal(1)
        assert result == Decimal("0.01")

        result = from_cents_decimal(10)
        assert result == Decimal("0.10")


# =============================================================================
# format_currency() 测试
# =============================================================================

class TestFormatCurrency:
    """测试 format_currency 函数"""

    # -------------------------------------------------------------------------
    # 正常路径测试
    # -------------------------------------------------------------------------

    def test_cny_default(self):
        """测试默认货币（CNY）"""
        assert format_currency(2990) == "¥29.90"
        assert format_currency(10000) == "¥100.00"

    def test_explicit_cny(self):
        """测试显式指定 CNY"""
        assert format_currency(2990, "CNY") == "¥29.90"

    def test_usd(self):
        """测试美元"""
        assert format_currency(2990, "USD") == "$29.90"

    def test_eur(self):
        """测试欧元"""
        assert format_currency(2990, "EUR") == "€29.90"

    def test_gbp(self):
        """测试英镑"""
        assert format_currency(2990, "GBP") == "£29.90"

    def test_jpy(self):
        """测试日元"""
        assert format_currency(2990, "JPY") == "¥29.90"

    def test_hkd(self):
        """测试港币"""
        assert format_currency(2990, "HKD") == "HK$29.90"

    def test_sgd(self):
        """测试新加坡元"""
        assert format_currency(2990, "SGD") == "S$29.90"

    def test_unknown_currency(self):
        """测试未知货币代码（使用代码 + 空格）"""
        assert format_currency(2990, "XXX") == "XXX 29.90"
        assert format_currency(100, "AUD") == "AUD 1.00"

    def test_negative_values(self):
        """测试负数"""
        assert format_currency(-1550) == "-¥15.50"
        assert format_currency(-100, "USD") == "-$1.00"

    def test_zero(self):
        """测试零值"""
        assert format_currency(0) == "¥0.00"


# =============================================================================
# 集成测试
# =============================================================================

class TestAmountConversionIntegration:
    """金额转换集成测试"""

    def test_round_trip_string_to_cents_to_string(self):
        """测试往返转换：字符串 -> 分 -> 字符串"""
        original = "29.90"
        cents = to_cents(original)
        result = from_cents(cents)
        assert result == original

    def test_round_trip_float_to_cents_to_string(self):
        """测试往返转换：浮点数 -> 分 -> 字符串"""
        original_float = 29.9
        cents = to_cents(original_float)
        result = from_cents(cents)
        assert result == "29.90"

    def test_round_trip_decimal_to_cents_to_decimal(self):
        """测试往返转换：Decimal -> 分 -> Decimal"""
        original = Decimal("29.90")
        cents = to_cents(original)
        result = from_cents_decimal(cents)
        assert result == original

    def test_calculation_with_decimals(self):
        """测试使用 Decimal 进行计算"""
        amount1 = from_cents_decimal(2990)  # 29.90
        amount2 = from_cents_decimal(1000)  # 10.00
        total = amount1 + amount2
        assert total == Decimal("39.90")

    def test_currency_formatting_workflow(self):
        """测试完整的货币格式化工作流"""
        # 用户输入: "29.9"
        cents = to_cents("29.9")  # 2990
        # 存储到数据库: 2990
        # 显示给用户: "¥29.90"
        display = format_currency(cents)
        assert display == "¥29.90"
