"""Pytest 配置和共享 Fixtures

这个文件包含所有测试共享的 fixtures 和配置。
"""

import json
import sqlite3
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner


# =============================================================================
# 数据库 Fixtures
# =============================================================================

@pytest.fixture
def memory_db() -> sqlite3.Connection:
    """创建内存数据库连接

    每个使用此 fixture 的测试都会获得一个独立的内存数据库。
    数据库在测试结束后自动关闭。

    Yields:
        sqlite3.Connection: 配置好 row_factory 的连接对象
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def memory_db_with_schema(memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """创建带有初始 schema 的内存数据库

    包含 cang_meta 表。

    Yields:
        sqlite3.Connection: 已初始化 schema 的连接对象
    """
    # 创建 cang_meta 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS cang_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    memory_db.commit()
    yield memory_db


@pytest.fixture
def temp_db_file(tmp_path: Path) -> tuple[sqlite3.Connection, Path]:
    """创建临时数据库文件

    使用 pytest 的 tmp_path fixture 创建临时文件。
    临时文件会在测试会话结束后自动清理。

    Args:
        tmp_path: pytest 提供的临时目录

    Yields:
        tuple[sqlite3.Connection, Path]: (连接对象, 数据库文件路径)
    """
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    yield conn, db_path
    conn.close()


# =============================================================================
# CLI Fixtures
# =============================================================================

@pytest.fixture
def cli_runner() -> CliRunner:
    """创建 Typer CLI 测试运行器

    用于测试 CLI 命令的输入输出。
    扩展了 .json() 方法用于解析 JSON 输出。

    Returns:
        CliRunner: Typer 的测试运行器实例
    """
    runner = CliRunner()
    original_invoke = runner.invoke

    def enhanced_invoke(*args, **kwargs):
        result = original_invoke(*args, **kwargs)

        def _json() -> dict:
            return json.loads(result.stdout.strip())

        result.json = _json
        return result

    runner.invoke = enhanced_invoke
    return runner


# =============================================================================
# JSON 响应验证 Helpers
# =============================================================================

class JSONResponseValidator:
    """JSON 响应验证辅助类"""

    @staticmethod
    def parse(output: str) -> dict:
        """解析 JSON 输出

        Args:
            output: CLI 输出的 JSON 字符串

        Returns:
            dict: 解析后的字典

        Raises:
            json.JSONDecodeError: JSON 格式错误
        """
        return json.loads(output)

    @staticmethod
    def assert_success(output: str) -> dict:
        """断言响应为成功格式

        验证:
        - success 为 True
        - 包含 data 字段
        - 不包含 error 字段

        Args:
            output: CLI 输出

        Returns:
            dict: data 字段内容

        Raises:
            AssertionError: 格式验证失败
        """
        data = JSONResponseValidator.parse(output)
        assert data["success"] is True, f"Expected success=True, got: {data}"
        assert "data" in data, f"Missing 'data' field in: {data}"
        assert "error" not in data, f"Unexpected 'error' field in: {data}"
        return data["data"]

    @staticmethod
    def assert_error(output: str, expected_code: str | None = None) -> dict:
        """断言响应为错误格式

        验证:
        - success 为 False
        - 包含 error 字段
        - error 包含 code 和 message
        - 可选验证 code 匹配

        Args:
            output: CLI 输出
            expected_code: 期望的错误代码

        Returns:
            dict: error 字段内容

        Raises:
            AssertionError: 格式验证失败
        """
        data = JSONResponseValidator.parse(output)
        assert data["success"] is False, f"Expected success=False, got: {data}"
        assert "error" in data, f"Missing 'error' field in: {data}"
        assert "data" not in data, f"Unexpected 'data' field in: {data}"

        error = data["error"]
        assert "code" in error, f"Missing 'code' in error: {error}"
        assert "message" in error, f"Missing 'message' in error: {error}"

        if expected_code:
            assert error["code"] == expected_code, f"Expected code={expected_code}, got: {error}"

        return error


@pytest.fixture
def json_validator() -> type[JSONResponseValidator]:
    """提供 JSON 响应验证器

    Returns:
        type[JSONResponseValidator]: 验证器类
    """
    return JSONResponseValidator


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_db_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Mock 数据库路径为临时目录

    用于避免测试污染用户主目录的 ~/.cang/

    Args:
        monkeypatch: pytest monkeypatch fixture
        tmp_path: pytest 临时目录

    Returns:
        Path: 临时数据库路径
    """
    test_db_path = tmp_path / ".cang" / "cang.db"

    def mock_get_db_path() -> Path:
        test_db_path.parent.mkdir(parents=True, exist_ok=True)
        return test_db_path

    # 导入前需要 mock，这里假设模块已导入
    # 实际使用时需要在测试中手动 patch
    return test_db_path


# =============================================================================
# 测试数据 Fixtures
# =============================================================================

@pytest.fixture
def sample_account_data() -> dict:
    """示例账户数据

    Returns:
        dict: 符合 accounts 表结构的示例数据
    """
    return {
        "name": "招商银行",
        "type": "checking",
        "balance_cents": 100000,
        "currency": "CNY",
        "is_active": True,
    }


@pytest.fixture
def sample_transaction_data() -> dict:
    """示例交易数据

    Returns:
        dict: 符合 transactions 表结构的示例数据
    """
    return {
        "account_id": 1,
        "amount_cents": -2990,
        "category": "餐饮",
        "payee": "麦当劳",
        "note": "午餐",
        "tx_date": "2026-03-15",
    }


# =============================================================================
# 数据库连接替换 Fixture（业务模块测试必备）
# =============================================================================

@pytest.fixture
def patch_db_connection(memory_db_with_full_schema: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch):
    """替换全局数据库连接为测试数据库

    这是测试 repository 模块的关键 fixture，使用方法：

    ```python
    def test_repository_function(patch_db_connection):
        from cang.fin.repository import list_accounts
        # 现在会使用测试数据库，而不是 ~/.cang/cang.db
        accounts = list_accounts()
    ```

    Args:
        memory_db_with_full_schema: 完整 schema 的测试数据库
        monkeypatch: pytest monkeypatch fixture

    Yields:
        None: 这个 fixture 只做副作用（替换连接）
    """
    from cang.db import connection as db_module

    # 替换全局连接
    monkeypatch.setattr(db_module, "_connection", memory_db_with_full_schema)

    # 清除 get_db_path 的缓存，确保使用测试连接
    if hasattr(db_module.get_db_path, "cache_clear"):
        db_module.get_db_path.cache_clear()

    yield


@pytest.fixture
def patch_db_connection_with_data(memory_db_with_sample_data: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch):
    """替换全局数据库连接为预填充数据的测试数据库

    与 patch_db_connection 类似，但数据库中已有示例数据。

    Args:
        memory_db_with_sample_data: 预填充数据的测试数据库
        monkeypatch: pytest monkeypatch fixture

    Yields:
        None
    """
    from cang.db import connection as db_module

    monkeypatch.setattr(db_module, "_connection", memory_db_with_sample_data)

    if hasattr(db_module.get_db_path, "cache_clear"):
        db_module.get_db_path.cache_clear()

    yield


# =============================================================================
# 完整 Schema Fixtures（用于业务模块测试）
# =============================================================================

@pytest.fixture
def memory_db_with_full_schema(memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """创建带有完整 schema 的内存数据库

    包含所有业务表：accounts, transactions, categories, transfers,
    invest_transactions, budgets, assets, cang_meta

    Yields:
        sqlite3.Connection: 已初始化完整 schema 的连接对象
    """
    # cang_meta 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS cang_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # accounts 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            currency TEXT DEFAULT 'CNY',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # transactions 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            account_id INTEGER REFERENCES accounts(id),
            category TEXT,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # categories 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # transfers 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_account_id INTEGER NOT NULL REFERENCES accounts(id),
            to_account_id INTEGER NOT NULL REFERENCES accounts(id),
            amount_cents INTEGER NOT NULL,
            fee_cents INTEGER DEFAULT 0,
            date TEXT NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # invest_transactions 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS invest_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            type TEXT NOT NULL,
            price_cents INTEGER NOT NULL,
            quantity REAL NOT NULL,
            amount_cents INTEGER NOT NULL,
            fee_cents INTEGER DEFAULT 0,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # budgets 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            period TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # assets 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            amount_cents INTEGER,
            value_cents INTEGER NOT NULL DEFAULT 0,
            currency TEXT DEFAULT 'CNY',
            code TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 设置 schema 版本
    memory_db.execute(
        "INSERT INTO cang_meta (key, value) VALUES ('schema_version', '1')"
    )

    memory_db.commit()
    yield memory_db


@pytest.fixture
def memory_db_with_sample_data(memory_db_with_full_schema: sqlite3.Connection) -> sqlite3.Connection:
    """创建包含示例数据的内存数据库

    在完整 schema 基础上，预填充常用的测试数据。

    Yields:
        sqlite3.Connection: 包含示例数据的连接对象
    """
    db = memory_db_with_full_schema

    # 插入示例账户
    db.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
               ("现金", "cash", "CNY"))
    db.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
               ("招商银行", "bank", "CNY"))
    db.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
               ("微信", "digital", "CNY"))
    db.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
               ("支付宝", "digital", "CNY"))

    # 插入示例分类
    categories = ["餐饮", "交通", "购物", "娱乐", "居住", "医疗", "教育", "通讯", "其他"]
    for cat in categories:
        db.execute("INSERT INTO categories (name) VALUES (?)", (cat,))

    # 插入示例交易
    db.execute("""INSERT INTO transactions (date, amount_cents, account_id, category, note)
                 VALUES (?, ?, ?, ?, ?)""", ("2026-03-15", -2990, 1, "餐饮", "午餐"))
    db.execute("""INSERT INTO transactions (date, amount_cents, account_id, category, note)
                 VALUES (?, ?, ?, ?, ?)""", ("2026-03-14", -5000, 2, "交通", "加油"))
    db.execute("""INSERT INTO transactions (date, amount_cents, account_id, category, note)
                 VALUES (?, ?, ?, ?, ?)""", ("2026-03-13", -15000, 3, "购物", "买衣服"))

    # 插入示例资产
    db.execute("""INSERT INTO assets (name, type, amount_cents, value_cents, currency, code)
                 VALUES (?, ?, ?, ?, ?, ?)""", ("现金", "cash", 10000, 10000, "CNY", None))
    db.execute("""INSERT INTO assets (name, type, amount_cents, value_cents, currency, code)
                 VALUES (?, ?, ?, ?, ?, ?)""", ("沪深300ETF", "fund", 5000, 520000, "CNY", "510300"))

    # 插入示例投资交易
    db.execute("""INSERT INTO invest_transactions (date, symbol, type, price_cents, quantity, amount_cents)
                 VALUES (?, ?, ?, ?, ?, ?)""", ("2026-03-01", "510300", "buy", 40000, 100, 4000000))
    db.execute("""INSERT INTO invest_transactions (date, symbol, type, price_cents, quantity, amount_cents)
                 VALUES (?, ?, ?, ?, ?, ?)""", ("2026-03-10", "510300", "buy", 41000, 20, 820000))

    # 插入示例预算
    db.execute("""INSERT INTO budgets (category, amount_cents, period, start_date, end_date)
                 VALUES (?, ?, ?, ?, ?)""", ("餐饮", 120000, "monthly", "2026-03-01", "2026-03-31"))
    db.execute("""INSERT INTO budgets (category, amount_cents, period, start_date, end_date)
                 VALUES (?, ?, ?, ?, ?)""", ("交通", 50000, "monthly", "2026-03-01", "2026-03-31"))

    db.commit()
    yield db


# =============================================================================
# 数据工厂 Fixtures
# =============================================================================

@pytest.fixture
def account_factory(memory_db_with_full_schema: sqlite3.Connection):
    """账户数据工厂

    用于快速创建测试账户。

    Yields:
        callable: 创建账户的函数
    """
    created_accounts = []

    def create_account(name: str, account_type: str = "checking", currency: str = "CNY") -> dict:
        """创建一个测试账户

        Args:
            name: 账户名称
            account_type: 账户类型
            currency: 货币代码

        Returns:
            dict: 创建的账户信息
        """
        cursor = memory_db_with_full_schema.execute(
            "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
            (name, account_type, currency)
        )
        account_id = cursor.lastrowid
        account = {
            "id": account_id,
            "name": name,
            "type": account_type,
            "currency": currency,
        }
        created_accounts.append(account)
        return account

    yield create_account

    # 清理
    if created_accounts:
        memory_db_with_full_schema.executemany(
            "DELETE FROM accounts WHERE id = ?",
            [(acc["id"],) for acc in created_accounts]
        )


@pytest.fixture
def transaction_factory(memory_db_with_full_schema: sqlite3.Connection):
    """交易数据工厂

    用于快速创建测试交易。

    Yields:
        callable: 创建交易的函数
    """
    created_transactions = []

    def create_transaction(
        account_id: int,
        amount_cents: int,
        date: str = "2026-03-15",
        category: str | None = None,
        note: str | None = None
    ) -> dict:
        """创建一个测试交易

        Args:
            account_id: 账户 ID
            amount_cents: 金额（分）
            date: 日期
            category: 分类
            note: 备注

        Returns:
            dict: 创建的交易信息
        """
        cursor = memory_db_with_full_schema.execute(
            """INSERT INTO transactions (date, amount_cents, account_id, category, note)
               VALUES (?, ?, ?, ?, ?)""",
            (date, amount_cents, account_id, category, note)
        )
        tx_id = cursor.lastrowid
        tx = {
            "id": tx_id,
            "date": date,
            "amount_cents": amount_cents,
            "account_id": account_id,
            "category": category,
            "note": note,
        }
        created_transactions.append(tx)
        return tx

    yield create_transaction

    # 清理
    if created_transactions:
        memory_db_with_full_schema.executemany(
            "DELETE FROM transactions WHERE id = ?",
            [(tx["id"],) for tx in created_transactions]
        )


@pytest.fixture
def asset_factory(memory_db_with_full_schema: sqlite3.Connection):
    """资产数据工厂

    用于快速创建测试资产。

    Yields:
        callable: 创建资产的函数
    """
    created_assets = []

    def create_asset(
        name: str,
        asset_type: str,
        value_cents: int,
        amount_cents: int | None = None,
        currency: str = "CNY",
        code: str | None = None
    ) -> dict:
        """创建一个测试资产

        Args:
            name: 资产名称
            asset_type: 资产类型
            value_cents: 市值（分）
            amount_cents: 持有数量（分）
            currency: 货币代码
            code: 资产代码

        Returns:
            dict: 创建的资产信息
        """
        cursor = memory_db_with_full_schema.execute(
            """INSERT INTO assets (name, type, amount_cents, value_cents, currency, code)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, asset_type, amount_cents, value_cents, currency, code)
        )
        asset_id = cursor.lastrowid
        asset = {
            "id": asset_id,
            "name": name,
            "type": asset_type,
            "amount_cents": amount_cents,
            "value_cents": value_cents,
            "currency": currency,
            "code": code,
        }
        created_assets.append(asset)
        return asset

    yield create_asset

    # 清理
    if created_assets:
        memory_db_with_full_schema.executemany(
            "DELETE FROM assets WHERE id = ?",
            [(asset["id"],) for asset in created_assets]
        )
