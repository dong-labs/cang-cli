"""Transfer 命令测试

测试 cang.fin.transfer 模块的所有命令。
"""

import sqlite3
import json
from datetime import date

import pytest
from typer.testing import CliRunner

from cang.fin.commands.transfer import app


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

    # 创建 transfers 表
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

    # 创建 transactions 表（转账会创建交易记录）
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
def sample_accounts(fin_db: sqlite3.Connection) -> tuple[dict, dict]:
    """创建两个示例账户"""
    cur = fin_db.cursor()
    cur.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                ("招商银行", "bank", "CNY"))
    acc1_id = cur.lastrowid
    cur.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                ("支付宝", "alipay", "CNY"))
    acc2_id = cur.lastrowid
    fin_db.commit()

    return (
        {"id": acc1_id, "name": "招商银行", "type": "bank"},
        {"id": acc2_id, "name": "支付宝", "type": "alipay"}
    )


@pytest.fixture
def cli_runner() -> CliRunner:
    """创建 CLI 测试运行器"""
    return CliRunner()


# ============================================================================
# Test transfer_cmd
# ============================================================================

class TestTransferCmd:
    """测试 cang fin transfer transfer 命令"""

    def test_basic_transfer(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试基本转账"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["from"] == f"招商银行 (ID:{acc1['id']})"
        assert data["data"]["to"] == f"支付宝 (ID:{acc2['id']})"
        assert data["data"]["amount"] == "100.00"
        assert data["data"]["fee"] == "0.00"

    def test_transfer_with_fee(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试带手续费的转账"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100",
            "--fee", "2.5"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["amount"] == "100.00"
        assert data["data"]["fee"] == "2.50"
        assert data["data"]["total_deducted"] == "102.50"

    def test_transfer_with_note(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试带备注的转账"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100",
            "--note", "转生活费"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True

    def test_transfer_with_custom_date(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试指定日期的转账"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100",
            "--date", "2026-03-10"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["date"] == "2026-03-10"

    def test_transfer_creates_transactions(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试转账创建了对应的交易记录"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100"
        ])
        assert result.exit_code == 0

        # 检查创建了交易记录
        cur = fin_db.cursor()
        cur.execute("SELECT COUNT(*) FROM transactions")
        count = cur.fetchone()[0]
        # 应该创建两条交易：转出账户扣款，转入账户收款
        assert count == 2

    def test_transfer_from_nonexistent_account_error(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试从不存在的账户转出返回错误"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", "999",
            "--to", str(acc2["id"]),
            "--amount", "100"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_transfer_to_nonexistent_account_error(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试转账到不存在的账户返回错误"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", "999",
            "--amount", "100"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_transfer_to_same_account_error(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试转账到同一账户返回错误"""
        acc1, _ = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc1["id"]),
            "--amount", "100"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_transfer_with_zero_amount_error(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试零金额转账返回错误"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "0"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_INPUT"

    def test_transfer_with_negative_amount_error(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试负金额转账返回错误"""
        acc1, acc2 = sample_accounts

        result = cli_runner.invoke(app, [
            "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "-100"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False


# ============================================================================
# Test list_transfer
# ============================================================================

class TestListTransfer:
    """测试 cang fin transfer ls 命令"""

    def test_empty_list(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试空转账列表"""
        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["transfers"] == []
        assert data["data"]["count"] == 0

    def test_list_single_transfer(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试列出单条转账"""
        acc1, acc2 = sample_accounts

        # 直接创建转账记录
        cur = fin_db.cursor()
        cur.execute(
            """INSERT INTO transfers (from_account_id, to_account_id, amount_cents, date)
               VALUES (?, ?, ?, ?)""",
            (acc1["id"], acc2["id"], 10000, "2026-03-15")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert len(data["data"]["transfers"]) == 1
        assert data["data"]["count"] == 1

    def test_list_multiple_transfers(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试列出多条转账"""
        acc1, acc2 = sample_accounts
        cur = fin_db.cursor()

        for i in range(3):
            cur.execute(
                """INSERT INTO transfers (from_account_id, to_account_id, amount_cents, date)
                   VALUES (?, ?, ?, ?)""",
                (acc1["id"], acc2["id"], 10000 * (i + 1), f"2026-03-{10 + i}")
            )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        data = json.loads(result.stdout)
        assert data["data"]["count"] == 3

    def test_list_with_limit(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试限制返回数量"""
        acc1, acc2 = sample_accounts
        cur = fin_db.cursor()

        for i in range(5):
            cur.execute(
                """INSERT INTO transfers (from_account_id, to_account_id, amount_cents, date)
                   VALUES (?, ?, ?, ?)""",
                (acc1["id"], acc2["id"], 10000, f"2026-03-{10 + i}")
            )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls", "--limit", "3"])
        data = json.loads(result.stdout)
        assert data["data"]["count"] == 3

    def test_transfers_order_by_date_desc(self, fin_db: sqlite3.Connection, sample_accounts: tuple, cli_runner: CliRunner):
        """测试转账按日期倒序排列"""
        acc1, acc2 = sample_accounts
        cur = fin_db.cursor()

        cur.execute(
            "INSERT INTO transfers (from_account_id, to_account_id, amount_cents, date) VALUES (?, ?, ?, ?)",
            (acc1["id"], acc2["id"], 10000, "2026-03-10")
        )
        cur.execute(
            "INSERT INTO transfers (from_account_id, to_account_id, amount_cents, date) VALUES (?, ?, ?, ?)",
            (acc1["id"], acc2["id"], 20000, "2026-03-15")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        data = json.loads(result.stdout)

        # 最新的在前
        assert data["data"]["transfers"][0]["date"] == "2026-03-15"
        assert data["data"]["transfers"][1]["date"] == "2026-03-10"
