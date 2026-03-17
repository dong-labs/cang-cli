"""Transaction 命令测试

测试 cang.fin.tx 模块的所有命令。
"""

import sqlite3
import json
from datetime import date
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from cang.fin.commands.tx import app, _parse_period


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

    # 创建 transactions 表
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
def sample_account(fin_db: sqlite3.Connection) -> dict:
    """创建示例账户"""
    cur = fin_db.cursor()
    cur.execute("INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
                ("招商银行", "bank", "CNY"))
    fin_db.commit()
    return {"id": cur.lastrowid, "name": "招商银行", "type": "bank"}


@pytest.fixture
def cli_runner() -> CliRunner:
    """创建 CLI 测试运行器"""
    return CliRunner()


# ============================================================================
# Test _parse_period 辅助函数
# ============================================================================

class TestParsePeriod:
    """测试 _parse_period 辅助函数"""

    @pytest.fixture
    def mock_today(self):
        """Mock 今天的日期为 2026-03-15 (周一)"""
        with patch('cang.fin.commands.tx.date') as mock_date:
            mock_date.today.return_value = date(2026, 3, 15)
            yield mock_date

    def test_parse_today(self, mock_today):
        """测试解析 today 期间"""
        start, end = _parse_period("today")
        assert start == "2026-03-15"
        assert end == "2026-03-15"

    def test_parse_week(self, mock_today):
        """测试解析 week 期间（本周一到今天）"""
        start, end = _parse_period("week")
        # 2026-03-15 是周日(weekday=6)，周一是 2026-03-09
        assert start == "2026-03-09"
        assert end == "2026-03-15"

    def test_parse_month(self, mock_today):
        """测试解析 month 期间（本月1日到今天）"""
        start, end = _parse_period("month")
        assert start == "2026-03-01"
        assert end == "2026-03-15"

    def test_parse_quarter(self, mock_today):
        """测试解析 quarter 期间（本季度首日到今天）"""
        start, end = _parse_period("quarter")
        # Q1: 1月1日
        assert start == "2026-01-01"
        assert end == "2026-03-15"

    def test_parse_year(self, mock_today):
        """测试解析 year 期间（今年1月1日到今天）"""
        start, end = _parse_period("year")
        assert start == "2026-01-01"
        assert end == "2026-03-15"

    def test_parse_invalid_period(self):
        """测试解析无效期间"""
        with pytest.raises(Exception):  # InvalidInputError
            _parse_period("invalid_period")


# ============================================================================
# Test list_tx
# ============================================================================

class TestListTx:
    """测试 cang fin tx ls 命令"""

    def test_empty_list(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试空交易列表"""
        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["transactions"] == []
        assert data["data"]["count"] == 0
        assert data["data"]["total"] == 0

    def test_list_transactions(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试列出交易"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category, note) VALUES (?, ?, ?, ?, ?)",
            ("2026-03-15", -2990, sample_account["id"], "餐饮", "午餐")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert len(data["data"]["transactions"]) == 1
        assert data["data"]["transactions"][0]["category"] == "餐饮"

    def test_filter_by_account(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试按账户筛选"""
        cur = fin_db.cursor()
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("支付宝", "alipay"))
        acc2_id = cur.lastrowid

        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            ("2026-03-15", -1000, sample_account["id"], "餐饮")
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            ("2026-03-15", -2000, acc2_id, "交通")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls", "--account", str(sample_account["id"])])
        data = json.loads(result.stdout)
        assert len(data["data"]["transactions"]) == 1

    def test_filter_by_category(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试按分类筛选"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            ("2026-03-15", -1000, sample_account["id"], "餐饮")
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            ("2026-03-15", -2000, sample_account["id"], "交通")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls", "--category", "餐饮"])
        data = json.loads(result.stdout)
        assert len(data["data"]["transactions"]) == 1

    def test_limit(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试限制数量"""
        cur = fin_db.cursor()
        for i in range(5):
            cur.execute(
                "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
                (f"2026-03-{10+i}", -1000, sample_account["id"])
            )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls", "--limit", "3"])
        data = json.loads(result.stdout)
        assert data["data"]["count"] == 3
        assert data["data"]["total"] == 5

    def test_offset(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试偏移量"""
        cur = fin_db.cursor()
        for i in range(5):
            cur.execute(
                "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
                (f"2026-03-{10+i}", -1000 * (i+1), sample_account["id"])
            )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls", "--offset", "2"])
        data = json.loads(result.stdout)
        assert data["data"]["count"] == 3  # 5 - 2 = 3

    def test_date_range_filter(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试日期范围筛选"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-10", -1000, sample_account["id"])
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-15", -2000, sample_account["id"])
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-20", -3000, sample_account["id"])
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls", "--start", "2026-03-12", "--end", "2026-03-18"])
        data = json.loads(result.stdout)
        assert len(data["data"]["transactions"]) == 1
        assert data["data"]["transactions"][0]["date"] == "2026-03-15"


# ============================================================================
# Test add_tx
# ============================================================================

class TestAddTx:
    """测试 cang fin tx add 命令"""

    def test_add_basic_expense(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试添加基本支出"""
        result = cli_runner.invoke(app, [
            "add",
            "--amount", "-29.9",
            "--account", str(sample_account["id"])
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["transaction"]["amount_cents"] == -2990
        assert data["data"]["message"] == "Transaction added"

    def test_add_income(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试添加收入"""
        result = cli_runner.invoke(app, [
            "add",
            "--amount", "1000",
            "--account", str(sample_account["id"]),
            "--category", "工资"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["transaction"]["amount_cents"] == 100000

    def test_add_with_category_and_note(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试添加带分类和备注的交易"""
        result = cli_runner.invoke(app, [
            "add",
            "--amount", "-29.9",
            "--account", str(sample_account["id"]),
            "--category", "餐饮",
            "--note", "午餐"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        tx = data["data"]["transaction"]
        assert tx["category"] == "餐饮"
        assert tx["note"] == "午餐"

    def test_add_with_custom_date(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试添加指定日期的交易"""
        result = cli_runner.invoke(app, [
            "add",
            "--amount", "-29.9",
            "--account", str(sample_account["id"]),
            "--date", "2026-03-10"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["transaction"]["date"] == "2026-03-10"

    def test_add_with_nonexistent_account_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加到不存在的账户返回错误"""
        result = cli_runner.invoke(app, [
            "add",
            "--amount", "-29.9",
            "--account", "999"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


# ============================================================================
# Test get_tx
# ============================================================================

class TestGetTx:
    """测试 cang fin tx get 命令"""

    def test_get_existing_transaction(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试获取存在的交易"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            ("2026-03-15", -2990, sample_account["id"], "餐饮")
        )
        fin_db.commit()
        tx_id = cur.lastrowid

        result = cli_runner.invoke(app, ["get", "--id", str(tx_id)])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["transaction"]["id"] == tx_id

    def test_get_nonexistent_transaction_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试获取不存在的交易返回错误"""
        result = cli_runner.invoke(app, ["get", "--id", "999"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


# ============================================================================
# Test update_tx
# ============================================================================

class TestUpdateTx:
    """测试 cang fin tx update 命令"""

    def test_update_amount(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试更新金额"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-15", -2990, sample_account["id"])
        )
        fin_db.commit()
        tx_id = cur.lastrowid

        result = cli_runner.invoke(app, [
            "update",
            "--id", str(tx_id),
            "--amount", "-39.9"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["transaction"]["amount_cents"] == -3990

    def test_update_category(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试更新分类"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            ("2026-03-15", -2990, sample_account["id"], "餐饮")
        )
        fin_db.commit()
        tx_id = cur.lastrowid

        result = cli_runner.invoke(app, [
            "update",
            "--id", str(tx_id),
            "--category", "交通"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["transaction"]["category"] == "交通"

    def test_update_nonexistent_transaction_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试更新不存在的交易返回错误"""
        result = cli_runner.invoke(app, [
            "update",
            "--id", "999",
            "--amount", "-10"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_update_with_invalid_account_error(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试更新到不存在的账户返回错误"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-15", -2990, sample_account["id"])
        )
        fin_db.commit()
        tx_id = cur.lastrowid

        result = cli_runner.invoke(app, [
            "update",
            "--id", str(tx_id),
            "--account", "999"
        ])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False


# ============================================================================
# Test delete_tx
# ============================================================================

class TestDeleteTx:
    """测试 cang fin tx delete 命令"""

    def test_delete_existing_transaction(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试删除存在的交易"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-15", -2990, sample_account["id"])
        )
        fin_db.commit()
        tx_id = cur.lastrowid

        result = cli_runner.invoke(app, ["delete", "--id", str(tx_id)])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["id"] == tx_id

        # 验证已删除
        cur.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
        assert cur.fetchone() is None

    def test_delete_nonexistent_transaction_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试删除不存在的交易返回错误"""
        result = cli_runner.invoke(app, ["delete", "--id", "999"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


# ============================================================================
# Test summary
# ============================================================================

class TestSummary:
    """测试 cang fin tx summary 命令"""

    def test_summary_default_month(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试默认本月汇总"""
        cur = fin_db.cursor()
        # 本月交易
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (date.today().isoformat(), 100000, sample_account["id"], "工资")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["summary"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        # 当没有指定 --period 时，默认使用本月但 period 标记为 custom
        assert data["data"]["period"] == "custom"
        # 验证日期范围是本月
        today = date.today()
        assert data["data"]["start_date"] == today.replace(day=1).isoformat()
        assert data["data"]["end_date"] == today.isoformat()

    def test_summary_with_period_today(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试今天汇总"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (date.today().isoformat(), -1000, sample_account["id"], "餐饮")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["summary", "--period", "today"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["data"]["period"] == "today"

    def test_summary_calculates_income_expense(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试汇总计算收入和支出"""
        cur = fin_db.cursor()
        today = date.today().isoformat()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (today, 100000, sample_account["id"], "工资")
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (today, -2990, sample_account["id"], "餐饮")
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (today, -5000, sample_account["id"], "交通")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["summary", "--period", "today"])
        data = json.loads(result.stdout)

        assert data["data"]["income_cents"] == 100000
        assert data["data"]["expense_cents"] == 7990
        assert data["data"]["net_cents"] == 92010
        assert data["data"]["transaction_count"] == 3

    def test_summary_with_date_range(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试自定义日期范围汇总"""
        cur = fin_db.cursor()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-10", -1000, sample_account["id"])
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-15", -2000, sample_account["id"])
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            ("2026-03-20", -3000, sample_account["id"])
        )
        fin_db.commit()

        result = cli_runner.invoke(app, [
            "summary",
            "--start", "2026-03-12",
            "--end", "2026-03-18"
        ])
        data = json.loads(result.stdout)

        assert data["data"]["transaction_count"] == 1

    def test_summary_filter_by_account(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试按账户筛选汇总"""
        cur = fin_db.cursor()
        cur.execute("INSERT INTO accounts (name, type) VALUES (?, ?)", ("支付宝", "alipay"))
        acc2_id = cur.lastrowid

        today = date.today().isoformat()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            (today, -1000, sample_account["id"])
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id) VALUES (?, ?, ?)",
            (today, -2000, acc2_id)
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["summary", "--account", str(sample_account["id"])])
        data = json.loads(result.stdout)

        assert data["data"]["expense_cents"] == 1000

    def test_summary_filter_by_category(self, fin_db: sqlite3.Connection, sample_account: dict, cli_runner: CliRunner):
        """测试按分类筛选汇总"""
        cur = fin_db.cursor()
        today = date.today().isoformat()
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (today, -1000, sample_account["id"], "餐饮")
        )
        cur.execute(
            "INSERT INTO transactions (date, amount_cents, account_id, category) VALUES (?, ?, ?, ?)",
            (today, -2000, sample_account["id"], "交通")
        )
        fin_db.commit()

        result = cli_runner.invoke(app, ["summary", "--category", "餐饮"])
        data = json.loads(result.stdout)

        assert data["data"]["expense_cents"] == 1000
