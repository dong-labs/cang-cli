"""测试辅助函数模块

提供测试中常用的辅助函数和工具。
"""

from datetime import datetime, timedelta
from typing import Any


def today_str() -> str:
    """获取今天的日期字符串 (YYYY-MM-DD)

    Returns:
        str: 今天的日期字符串
    """
    return datetime.now().strftime("%Y-%m-%d")


def yesterday_str() -> str:
    """获取昨天的日期字符串 (YYYY-MM-DD)

    Returns:
        str: 昨天的日期字符串
    """
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def days_ago_str(days: int) -> str:
    """获取 N 天前的日期字符串 (YYYY-MM-DD)

    Args:
        days: 天数

    Returns:
        str: N 天前的日期字符串
    """
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def assert_lists_equal(dict_lists: list[dict], key: str, expected_values: list[Any]) -> None:
    """断言字典列表中指定键的值等于期望值

    Args:
        dict_lists: 字典列表
        key: 要检查的键
        expected_values: 期望的值列表

    Raises:
        AssertionError: 如果值不匹配
    """
    actual_values = [d.get(key) for d in dict_lists]
    assert actual_values == expected_values, f"Expected {expected_values}, got {actual_values}"


def sort_by_id(items: list[dict]) -> list[dict]:
    """按 id 对字典列表进行排序

    Args:
        items: 字典列表

    Returns:
        list[dict]: 排序后的列表
    """
    return sorted(items, key=lambda x: x.get("id", 0))


def sum_field(items: list[dict], field: str) -> int:
    """对字典列表中指定字段的值求和

    Args:
        items: 字典列表
        field: 要求和的字段

    Returns:
        int: 总和
    """
    return sum(item.get(field, 0) for item in items)
