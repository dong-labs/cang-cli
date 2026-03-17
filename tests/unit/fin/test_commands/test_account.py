"""Account 命令测试

测试 cang.fin.account 模块的所有命令。
"""

import sqlite3
import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cang.fin.commands.account import app, ACCOUNT_TYPES


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def fin_db(memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """创建带有 fin 模块表结构的内存数据库"""
    # 创建 accounts 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            currency TEXT DEFAULT 'CNY',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 创建 transactions 表（用于 balance 测试）
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

    memory_db.commit()

    # Mock 全局数据库连接
    import cang.db.connection as conn_module
    original_get_connection = conn_module.get_connection

    def mock_get_connection():
        return memory_db

    conn_module.get_connection = mock_get_connection

    yield memory_db

    # 恢复原始函数
    conn_module.get_connection = original_get_connection


@pytest.fixture
def cli_runner() -> CliRunner:
    """创建 CLI 测试运行器"""
    return CliRunner()


# ============================================================================
# Test list_accounts_cmd
# ============================================================================

class TestListAccountsCmd:
    """测试 cang fin account ls 命令"""

    def test_empty_list(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试空账户列表"""
        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["accounts"] == []

    def test_list_single_account(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试列出单个账户"""
        # 先创建账户
        fin_db.execute(
            "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
            ("招商银行", "bank", "CNY")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["accounts"]) == 1
        assert data["data"]["accounts"][0]["name"] == "招商银行"

    def test_list_multiple_accounts(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试列出多个账户"""
        for name, acc_type in [("现金", "cash"), ("支付宝", "alipay"), ("信用卡", "credit")]:
            fin_db.execute(
                "INSERT INTO accounts (name, type) VALUES (?, ?)",
                (name, acc_type)
            )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert len(data["data"]["accounts"]) == 3
        names = [a["name"] for a in data["data"]["accounts"]]
        assert "现金" in names
        assert "支付宝" in names
        assert "信用卡" in names


# ============================================================================
# Test add_account
# ============================================================================

class TestAddAccount:
    """测试 cang fin account add 命令"""

    def test_add_basic_account(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加基本账户"""
        result = cli_runner.invoke(app, [
            "add",
            "--name", "招商银行",
            "--type", "bank"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["name"] == "招商银行"
        assert data["data"]["type"] == "bank"
        assert data["data"]["currency"] == "CNY"

    def test_add_with_custom_currency(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加指定货币的账户"""
        result = cli_runner.invoke(app, [
            "add",
            "--name", "USD Account",
            "--type", "bank",
            "--currency", "USD"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["currency"] == "USD"

    def test_add_with_duplicate_name_returns_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加重复名称账户返回错误"""
        # 第一次添加成功
        cli_runner.invoke(app, ["add", "--name", "重复", "--type", "bank"])

        # 第二次添加同名账户
        result = cli_runner.invoke(app, ["add", "--name", "重复", "--type", "cash"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "ALREADY_EXISTS"

    def test_add_with_invalid_type_returns_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试无效账户类型返回错误"""
        result = cli_runner.invoke(app, [
            "add",
            "--name", "测试账户",
            "--type", "invalid_type"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_all_valid_account_types(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试所有有效的账户类型"""
        for acc_type in ACCOUNT_TYPES:
            result = cli_runner.invoke(app, [
                "add",
                "--name", f"{acc_type}_account",
                "--type", acc_type
            ])
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["success"] is True


# ============================================================================
# Test get_account
# ============================================================================

class TestGetAccount:
    """测试 cang fin account get 命令"""

    def test_get_existing_account(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试获取存在的账户"""
        cur = fin_db.cursor()
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("招商银行", "bank"))
        fin_db.commit()
        account_id = cur.lastrowid

        result = cli_runner.invoke(app, ["get", "--id", str(account_id)])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["account"]["name"] == "招商银行"

    def test_get_nonexistent_account_returns_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试获取不存在的账户返回错误"""
        result = cli_runner.invoke(app, ["get", "--id", "999"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_get_with_zero_id(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试 ID 为 0"""
        result = cli_runner.invoke(app, ["get", "--id", "0"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False


# ============================================================================
# Test account_balance
# ============================================================================

class TestAccountBalance:
    """测试 cang fin account balance 命令"""

    def test_all_accounts_balance(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试获取所有账户余额"""
        # 创建账户和交易
        cur = fin_db.cursor()
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("现金", "cash"))
        acc1_id = cur.lastrowid
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("银行", "bank"))
        acc2_id = cur.lastrowid

        # 添加交易
        cur.execute("INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
                    ("2026-03-15", 10000, acc1_id))
        cur.execute("INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
                    ("2026-03-15", -5000, acc2_id))
        fin_db.commit()

        result = cli_runner.invoke(app, ["balance"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["balances"]) == 2

    def test_single_account_balance(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试获取单个账户余额"""
        cur = fin_db.cursor()
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("现金", "cash"))
        acc_id = cur.lastrowid
        cur.execute("INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
                    ("2026-03-15", 12345, acc_id))
        fin_db.commit()

        result = cli_runner.invoke(app, ["balance", "--account-id", str(acc_id)])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["account_id"] == acc_id
        assert data["data"]["balance"] == "123.45"

    def test_balance_nonexistent_account_returns_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试查询不存在账户的余额返回错误"""
        result = cli_runner.invoke(app, ["balance", "--account-id", "999"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_zero_balance(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试零余额"""
        cur = fin_db.cursor()
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("新账户", "bank"))
        acc_id = cur.lastrowid
        fin_db.commit()

        result = cli_runner.invoke(app, ["balance", "--account-id", str(acc_id)])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["balance"] == "0.00"
