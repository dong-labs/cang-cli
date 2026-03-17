"""金额转换工具

职责:
- 用户友好格式 <-> 内部存储格式 (分)
- 处理 CLI 输入/输出中的金额转换
- 提供货币格式化显示
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


# ============================================================================
# 金额转换
# ============================================================================

def to_cents(amount: float | str | int) -> int:
    """将用户友好的金额格式转换为分 (整数)

    支持负数（用于支出场景）。
    使用四舍五入确保精度正确。

    Args:
        amount: 输入金额，可以是 float、str 或 int

    Returns:
        int: 金额对应的分数

    Raises:
        ValueError: 当输入无法转换为有效金额时

    Examples:
        >>> to_cents(29.9)
        2990
        >>> to_cents("29.9")
        2990
        >>> to_cents(100)
        10000
        >>> to_cents(-15.5)
        -1550
    """
    try:
        # 转换为 Decimal 以确保精度
        if isinstance(amount, (int, float)):
            dec = Decimal(str(amount))
        else:
            # 字符串直接转换，去掉可能的空格
            dec = Decimal(str(amount).strip())

        # 乘以 100 并四舍五入到整数
        cents = (dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return int(cents)

    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError(f"Invalid amount: {amount!r}") from e


def from_cents(cents: int) -> str:
    """将分转换为格式化的金额字符串

    保留两位小数，支持负数。

    Args:
        cents: 金额的分数

    Returns:
        str: 格式化的金额字符串，保留两位小数

    Examples:
        >>> from_cents(2990)
        '29.90'
        >>> from_cents(10000)
        '100.00'
        >>> from_cents(0)
        '0.00'
        >>> from_cents(-1550)
        '-15.50'
    """
    return f"{cents / 100:.2f}"


def from_cents_decimal(cents: int) -> Decimal:
    """将分转换为 Decimal (用于计算)

    用于需要精确计算的场景，避免浮点数精度问题。

    Args:
        cents: 金额的分数

    Returns:
        Decimal: 金额对应的 Decimal 对象

    Examples:
        >>> from_cents_decimal(2990)
        Decimal('29.90')
    """
    return Decimal(cents) / Decimal("100")


# ============================================================================
# 货币格式化
# ============================================================================

# 货币符号映射
_CURRENCY_SYMBOLS = {
    "CNY": "¥",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "HKD": "HK$",
    "SGD": "S$",
}


def format_currency(cents: int, currency: str = "CNY") -> str:
    """格式化为货币显示

    Args:
        cents: 金额的分数
        currency: 货币代码，默认为 CNY

    Returns:
        str: 带货币符号的格式化金额字符串

    Examples:
        >>> format_currency(2990)
        '¥29.90'
        >>> format_currency(2990, "USD")
        '$29.90'
        >>> format_currency(-1550)
        '-¥15.50'
    """
    symbol = _CURRENCY_SYMBOLS.get(currency, currency + " ")
    amount = from_cents(cents)
    # 负数符号应该在货币符号之前
    if cents < 0:
        return f"-{symbol}{amount[1:]}"  # 去掉 amount 自带的负号
    return f"{symbol}{amount}"
