"""自定义断言模块

职责:
- 提供业务相关的断言函数
- 封装复杂的验证逻辑
- 提供更友好的错误消息
"""

from __future__ import annotations

import sqlite3
from typing import Any

from cang.db.schema import SCHEMA_VERSION


# =============================================================================
# 数据库断言
# =============================================================================

def assert_table_exists(conn: sqlite3.Connection, table_name: str) -> None:
    """断言表存在

    Args:
        conn: 数据库连接
        table_name: 表名

    Raises:
        AssertionError: 表不存在
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    result = cursor.fetchone()
    assert result is not None, f"Table '{table_name}' does not exist"


def assert_table_not_exists(conn: sqlite3.Connection, table_name: str) -> None:
    """断言表不存在

    Args:
        conn: 数据库连接
        table_name: 表名

    Raises:
        AssertionError: 表存在
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    result = cursor.fetchone()
    assert result is None, f"Table '{table_name}' exists but should not"


def assert_row_count(
    conn: sqlite3.Connection,
    table: str,
    expected: int,
    where: str | None = None,
) -> None:
    """断言表的行数

    Args:
        conn: 数据库连接
        table: 表名
        expected: 期望的行数
        where: WHERE 子句（不含 WHERE 关键字）

    Raises:
        AssertionError: 行数不匹配
    """
    query = f"SELECT COUNT(*) FROM {table}"
    params: list = []
    if where:
        query += f" WHERE {where}"

    cursor = conn.cursor()
    cursor.execute(query, params)
    actual = cursor.fetchone()[0]

    assert actual == expected, \
        f"Expected {expected} rows in '{table}', got {actual}"


def assert_row_exists(
    conn: sqlite3.Connection,
    table: str,
    conditions: dict[str, Any],
) -> None:
    """断言满足条件的行存在

    Args:
        conn: 数据库连接
        table: 表名
        conditions: 字段值条件字典

    Raises:
        AssertionError: 行不存在
    """
    where_clause = " AND ".join(f"{k} = ?" for k in conditions.keys())
    params = list(conditions.values())

    query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
    cursor = conn.cursor()
    cursor.execute(query, params)
    count = cursor.fetchone()[0]

    assert count > 0, f"No row found in '{table}' matching {conditions}"


def assert_row_not_exists(
    conn: sqlite3.Connection,
    table: str,
    conditions: dict[str, Any],
) -> None:
    """断言满足条件的行不存在

    Args:
        conn: 数据库连接
        table: 表名
        conditions: 字段值条件字典

    Raises:
        AssertionError: 行存在
    """
    where_clause = " AND ".join(f"{k} = ?" for k in conditions.keys())
    params = list(conditions.values())

    query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
    cursor = conn.cursor()
    cursor.execute(query, params)
    count = cursor.fetchone()[0]

    assert count == 0, f"Row found in '{table}' matching {conditions}, should not exist"


# =============================================================================
# Schema 断言
# =============================================================================

def assert_schema_version(conn: sqlite3.Connection, expected: str | None = None) -> None:
    """断言 Schema 版本

    Args:
        conn: 数据库连接
        expected: 期望的版本号，默认为 SCHEMA_VERSION

    Raises:
        AssertionError: 版本不匹配
    """
    if expected is None:
        expected = SCHEMA_VERSION

    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT value FROM cang_meta WHERE key = 'schema_version'"
        )
        result = cursor.fetchone()
        actual = result[0] if result else None
    except sqlite3.OperationalError:
        actual = None

    assert actual == expected, \
        f"Expected schema version '{expected}', got '{actual}'"


def assert_all_tables_exist(conn: sqlite3.Connection) -> None:
    """断言所有 Cang 表都已创建

    Args:
        conn: 数据库连接

    Raises:
        AssertionError: 有表缺失
    """
    expected_tables = {
        "cang_meta",
        "accounts",
        "transactions",
        "categories",
        "transfers",
        "invest_transactions",
        "budgets",
        "assets",
    }

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    actual_tables = {row[0] for row in cursor.fetchall()}

    missing = expected_tables - actual_tables
    assert not missing, f"Missing tables: {missing}"


# =============================================================================
# JSON 响应断言
# =============================================================================

def assert_json_response_structure(
    data: dict,
    has_data: bool = True,
    has_error: bool = False,
) -> None:
    """断言 JSON 响应结构

    Args:
        data: 解析后的 JSON 数据
        has_data: 是否应该有 data 字段
        has_error: 是否应该有 error 字段

    Raises:
        AssertionError: 结构不符合预期
    """
    assert "success" in data, "Missing 'success' field in response"

    if has_data:
        assert "data" in data, "Missing 'data' field in response"

    if has_error:
        assert "error" in data, "Missing 'error' field in response"
        error = data["error"]
        assert "code" in error, "Missing 'code' in error field"
        assert "message" in error, "Missing 'message' in error field"


def assert_success_response(data: dict) -> Any:
    """断言为成功响应并返回 data

    Args:
        data: 解析后的 JSON 数据

    Returns:
        data 字段内容

    Raises:
        AssertionError: 不是成功响应
    """
    assert data.get("success") is True, f"Expected success=True, got: {data}"
    assert "data" in data, f"Missing 'data' field in: {data}"
    assert "error" not in data, f"Unexpected 'error' field in: {data}"
    return data["data"]


def assert_error_response(
    data: dict,
    expected_code: str | None = None,
) -> dict:
    """断言为错误响应并返回 error

    Args:
        data: 解析后的 JSON 数据
        expected_code: 期望的错误代码

    Returns:
        error 字段内容

    Raises:
        AssertionError: 不是错误响应
    """
    assert data.get("success") is False, f"Expected success=False, got: {data}"
    assert "error" in data, f"Missing 'error' field in: {data}"
    assert "data" not in data, f"Unexpected 'data' field in: {data}"

    error = data["error"]
    assert "code" in error, f"Missing 'code' in error: {error}"
    assert "message" in error, f"Missing 'message' in error: {error}"

    if expected_code:
        assert error["code"] == expected_code, \
            f"Expected code={expected_code}, got: {error.get('code')}"

    return error


# =============================================================================
# 数值断言
# =============================================================================

def assert_amount_cents_equal(actual: int, expected_yuan: float) -> None:
    """断言金额（分）等于期望值（元）

    Args:
        actual: 实际金额（分）
        expected_yuan: 期望金额（元）

    Raises:
        AssertionError: 金额不匹配
    """
    expected_cents = int(expected_yuan * 100)
    assert actual == expected_cents, \
        f"Amount mismatch: {actual} cents != {expected_yuan} yuan ({expected_cents} cents)"


def assert_negative_amount_cents(amount_cents: int) -> None:
    """断言金额为负数（支出）

    Args:
        amount_cents: 金额（分）

    Raises:
        AssertionError: 金额不是负数
    """
    assert amount_cents < 0, f"Expected negative amount, got {amount_cents}"


def assert_positive_amount_cents(amount_cents: int) -> None:
    """断言金额为正数（收入）

    Args:
        amount_cents: 金额（分）

    Raises:
        AssertionError: 金额不是正数
    """
    assert amount_cents > 0, f"Expected positive amount, got {amount_cents}"


# =============================================================================
# 账户断言
# =============================================================================

def assert_account_data(
    account: dict,
    expected_name: str,
    expected_type: str,
    expected_currency: str = "CNY",
) -> None:
    """断言账户数据

    Args:
        account: 账户数据字典
        expected_name: 期望的账户名称
        expected_type: 期望的账户类型
        expected_currency: 期望的货币代码

    Raises:
        AssertionError: 数据不匹配
    """
    assert account["name"] == expected_name, \
        f"Account name mismatch: {account.get('name')} != {expected_name}"
    assert account["type"] == expected_type, \
        f"Account type mismatch: {account.get('type')} != {expected_type}"
    assert account["currency"] == expected_currency, \
        f"Account currency mismatch: {account.get('currency')} != {expected_currency}"


# =============================================================================
# 交易断言
# =============================================================================

def assert_transaction_data(
    tx: dict,
    expected_account_id: int | None = None,
    expected_category: str | None = None,
    expected_amount_cents: int | None = None,
) -> None:
    """断言交易数据

    Args:
        tx: 交易数据字典
        expected_account_id: 期望的账户 ID
        expected_category: 期望的分类
        expected_amount_cents: 期望的金额（分）

    Raises:
        AssertionError: 数据不匹配
    """
    if expected_account_id is not None:
        assert tx["account_id"] == expected_account_id, \
            f"Account ID mismatch: {tx.get('account_id')} != {expected_account_id}"

    if expected_category is not None:
        assert tx["category"] == expected_category, \
            f"Category mismatch: {tx.get('category')} != {expected_category}"

    if expected_amount_cents is not None:
        assert tx["amount_cents"] == expected_amount_cents, \
            f"Amount mismatch: {tx.get('amount_cents')} != {expected_amount_cents}"
