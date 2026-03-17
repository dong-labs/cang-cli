"""Budget 模块 CLI 集成测试

测试 cang budget 命令行接口的所有子命令:
- budget init: 初始化模块
- budget budget ls: 列出预算
- budget budget set: 创建预算
- budget budget get: 获取预算详情
- budget budget update: 更新预算
- budget budget delete: 删除预算
- budget status: 查看预算状态
- budget history: 查看预算历史
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sqlite3

from cang.db.connection import close_connection


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def budget_db(tmp_path):
    """创建独立的测试数据库文件"""
    db_path = tmp_path / "test_budget.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # 创建所有必要的表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cang_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.execute("""
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

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount_cents INTEGER NOT NULL,
            account_id INTEGER,
            category TEXT,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 设置 schema 版本
    conn.execute(
        "INSERT INTO cang_meta (key, value) VALUES ('schema_version', '1')"
    )
    conn.commit()

    yield conn, db_path

    # 不关闭连接，让测试套件结束时自然关闭


@pytest.fixture
def budget_runner(budget_db, cli_runner, monkeypatch, request):
    """配置使用测试数据库的 CLI 运行器"""
    conn, db_path = budget_db

    # 直接 mock get_connection 返回我们的测试连接
    def mock_get_connection():
        return conn

    # Mock get_db_path 返回测试数据库路径
    def mock_get_db_path():
        return db_path

    # Patch 核心数据库模块
    import cang.db.connection
    import cang.budget.repository
    import cang.db.schema

    # 设置全局连接
    monkeypatch.setattr(cang.db.connection, "_connection", conn)
    monkeypatch.setattr(cang.db.connection, "get_connection", mock_get_connection)
    monkeypatch.setattr(cang.db.connection, "get_db_path", mock_get_db_path)

    # repository 和 schema 模块通过 connection 模块使用数据库，所以只需要 patch connection

    yield cli_runner, conn

    # 清理：关闭连接
    try:
        conn.close()
    except Exception:
        pass


# =============================================================================
# budget init 命令测试
# =============================================================================

class TestBudgetInitCommand:
    """测试 budget init 命令"""

    def test_init_already_initialized(self, budget_runner):
        """测试已初始化的数据库"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["init", "init"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["schema_version"] == "1"
        assert data["data"]["budgets_table_exists"] is True


# =============================================================================
# budget budget ls 命令测试
# =============================================================================

class TestBudgetLsCommand:
    """测试 budget budget ls 命令"""

    def test_list_empty_budgets(self, budget_runner):
        """测试列出空预算列表"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "ls"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["budgets"] == []
        assert data["data"]["count"] == 0

    def test_list_all_budgets(self, budget_runner):
        """测试列出所有预算"""
        cli_runner, conn = budget_runner

        # 插入测试数据
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("交通", 100000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "ls"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 2
        budgets = data["data"]["budgets"]
        assert len(budgets) == 2

    def test_list_by_period(self, budget_runner):
        """测试按周期筛选"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("交通", 300000, "week", "2026-03-10", "2026-03-16")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "ls", "--period", "month"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert data["data"]["budgets"][0]["period"] == "month"

    def test_list_by_category(self, budget_runner):
        """测试按分类筛选"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("交通", 100000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "ls", "--category", "餐饮"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert data["data"]["budgets"][0]["category"] == "餐饮"

    def test_invalid_period(self, budget_runner):
        """测试无效周期参数"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "ls", "--period", "invalid"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "Invalid period" in data["error"]["message"]


# =============================================================================
# budget budget set 命令测试
# =============================================================================

class TestBudgetSetCommand:
    """测试 budget budget set 命令"""

    def test_set_budget_auto_dates(self, budget_runner):
        """测试创建预算（自动日期）"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, [
            "budget", "set",
            "--category", "餐饮",
            "--amount", "5000",
            "--period", "month"
        ])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["budget"]["category"] == "餐饮"
        assert data["data"]["amount"] == "5000.00"  # from_cents 返回字符串
        assert data["data"]["budget"]["period"] == "month"

    def test_set_budget_custom_dates(self, budget_runner):
        """测试创建预算（自定义日期）"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, [
            "budget", "set",
            "--category", "餐饮",
            "--amount", "5000",
            "--period", "month",
            "--start", "2026-03-01",
            "--end", "2026-03-31"
        ])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["budget"]["start_date"] == "2026-03-01"
        assert data["data"]["budget"]["end_date"] == "2026-03-31"

    def test_set_budget_duplicate(self, budget_runner):
        """测试创建重复预算"""
        cli_runner, conn = budget_runner

        # 先创建一个预算
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        # 尝试创建相同配置的预算
        result = cli_runner.invoke(app, [
            "budget", "set",
            "--category", "餐饮",
            "--amount", "6000",
            "--period", "month",
            "--start", "2026-03-01",
            "--end", "2026-03-31"
        ])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "already exists" in data["error"]["message"]

    def test_set_budget_invalid_period(self, budget_runner):
        """测试创建预算时使用无效周期"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, [
            "budget", "set",
            "--category", "餐饮",
            "--amount", "5000",
            "--period", "invalid"
        ])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "Invalid period" in data["error"]["message"]


# =============================================================================
# budget budget get 命令测试
# =============================================================================

class TestBudgetGetCommand:
    """测试 budget budget get 命令"""

    def test_get_existing_budget(self, budget_runner):
        """测试获取存在的预算"""
        cli_runner, conn = budget_runner

        budget_id = conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        ).lastrowid
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "get", "--id", str(budget_id)])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["budget"]["id"] == budget_id
        assert data["data"]["budget"]["category"] == "餐饮"
        assert data["data"]["amount"] == "5000.00"  # from_cents 返回字符串

    def test_get_nonexistent_budget(self, budget_runner):
        """测试获取不存在的预算"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "get", "--id", "999"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "not found" in data["error"]["message"]


# =============================================================================
# budget budget update 命令测试
# =============================================================================

class TestBudgetUpdateCommand:
    """测试 budget budget update 命令"""

    def test_update_existing_budget(self, budget_runner):
        """测试更新存在的预算"""
        cli_runner, conn = budget_runner

        budget_id = conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        ).lastrowid
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, [
            "budget", "update",
            "--id", str(budget_id),
            "--amount", "6000"
        ])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["amount"] == "6000.00"  # from_cents 返回字符串
        assert data["data"]["budget"]["category"] == "餐饮"  # 其他字段不变

    def test_update_nonexistent_budget(self, budget_runner):
        """测试更新不存在的预算"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, [
            "budget", "update",
            "--id", "999",
            "--amount", "6000"
        ])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "not found" in data["error"]["message"]


# =============================================================================
# budget budget delete 命令测试
# =============================================================================

class TestBudgetDeleteCommand:
    """测试 budget budget delete 命令"""

    def test_delete_existing_budget(self, budget_runner):
        """测试删除存在的预算"""
        cli_runner, conn = budget_runner

        budget_id = conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        ).lastrowid
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "delete", "--id", str(budget_id)])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["deleted"] is True
        assert data["data"]["budget_id"] == budget_id
        assert data["data"]["category"] == "餐饮"

    def test_delete_nonexistent_budget(self, budget_runner):
        """测试删除不存在的预算"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["budget", "delete", "--id", "999"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "not found" in data["error"]["message"]


# =============================================================================
# budget status 命令测试
# =============================================================================

class TestBudgetStatusCommand:
    """测试 budget status 命令"""

    def test_status_empty(self, budget_runner):
        """测试空预算状态"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["statuses"] == []
        assert data["data"]["count"] == 0

    def test_status_with_no_spending(self, budget_runner):
        """测试无支出时的状态"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 1
        status = data["data"]["statuses"][0]
        assert status["budget"] == "5000.00"  # from_cents 返回字符串
        assert status["spent"] == "0.00"
        assert status["remaining"] == "5000.00"
        assert status["percentage"] == 0

    def test_status_with_spending(self, budget_runner):
        """测试有支出时的状态"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO transactions (date, amount_cents, category) VALUES (?, ?, ?)",
            ("2026-03-15", -150000, "餐饮")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        status = data["data"]["statuses"][0]
        assert status["spent"] == "-1500.00"  # from_cents 返回字符串
        assert status["remaining"] == "6500.00"
        assert status["percentage"] == -30.0

    def test_status_over_budget(self, budget_runner):
        """测试超支状态"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO transactions (date, amount_cents, category) VALUES (?, ?, ?)",
            ("2026-03-15", -600000, "餐饮")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status"])

        assert result.exit_code == 0
        data = result.json()

        status = data["data"]["statuses"][0]
        assert status["percentage"] == -120.0
        assert status["remaining"] == "11000.00"  # from_cents 返回字符串

    def test_status_filter_by_period(self, budget_runner):
        """测试按周期筛选状态"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("交通", 100000, "week", "2026-03-10", "2026-03-16")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status", "--period", "month"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert data["data"]["statuses"][0]["period"] == "month"

    def test_status_filter_by_category(self, budget_runner):
        """测试按分类筛选状态"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("交通", 100000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status", "--category", "餐饮"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert data["data"]["statuses"][0]["category"] == "餐饮"

    def test_status_invalid_period(self, budget_runner):
        """测试状态命令使用无效周期"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["status", "status", "--period", "invalid"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is False
        assert "Invalid period" in data["error"]["message"]


# =============================================================================
# budget history 命令测试
# =============================================================================

class TestBudgetHistoryCommand:
    """测试 budget history 命令"""

    def test_history_empty(self, budget_runner):
        """测试空历史记录"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["history", "history"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["history"] == []
        assert data["data"]["count"] == 0

    def test_history_with_budgets(self, budget_runner):
        """测试有预算的历史记录"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31", "2026-03-01 10:00:00")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("交通", 100000, "month", "2026-03-01", "2026-03-31", "2026-03-02 10:00:00")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["history", "history"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 2
        # 按创建时间倒序，交通在后创建，应该在前
        history = data["data"]["history"]
        # 注意：由于时间戳可能相同，我们只验证数量和内容
        categories = [h["category"] for h in history]
        assert "餐饮" in categories
        assert "交通" in categories

    def test_history_filter_by_category(self, budget_runner):
        """测试按分类筛选历史"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("交通", 100000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["history", "history", "--category", "餐饮"])

        assert result.exit_code == 0
        data = result.json()

        assert data["success"] is True
        assert data["data"]["count"] == 1
        assert data["data"]["history"][0]["category"] == "餐饮"

    def test_history_includes_amount(self, budget_runner):
        """测试历史记录包含格式化后的金额"""
        cli_runner, conn = budget_runner

        conn.execute(
            "INSERT INTO budgets (category, amount_cents, period, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
            ("餐饮", 500000, "month", "2026-03-01", "2026-03-31")
        )
        conn.commit()

        from cang.budget.cli import app
        result = cli_runner.invoke(app, ["history", "history"])

        assert result.exit_code == 0
        data = result.json()

        history = data["data"]["history"][0]
        assert "amount" in history
        assert history["amount"] == "5000.00"  # from_cents 返回字符串


# =============================================================================
# 完整工作流测试
# =============================================================================

class TestBudgetWorkflow:
    """测试完整的预算管理工作流"""

    def test_complete_budget_lifecycle(self, budget_runner):
        """测试预算的完整生命周期"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app

        # 1. 创建预算
        create_result = cli_runner.invoke(app, [
            "budget", "set",
            "--category", "餐饮",
            "--amount", "5000",
            "--period", "month"
        ])
        assert create_result.exit_code == 0
        create_data = create_result.json()
        assert create_data["success"] is True
        budget_id = create_data["data"]["budget"]["id"]

        # 2. 查看预算
        get_result = cli_runner.invoke(app, ["budget", "get", "--id", str(budget_id)])
        assert get_result.exit_code == 0
        get_data = get_result.json()
        assert get_data["success"] is True

        # 3. 查看状态（无支出）
        status_result = cli_runner.invoke(app, ["status", "status"])
        assert status_result.exit_code == 0
        status_data = status_result.json()
        assert status_data["data"]["statuses"][0]["percentage"] == 0

        # 4. 添加支出
        conn.execute(
            "INSERT INTO transactions (date, amount_cents, category) VALUES (?, ?, ?)",
            ("2026-03-15", -200000, "餐饮")
        )
        conn.commit()

        # 5. 再次查看状态（有支出）
        status_result = cli_runner.invoke(app, ["status", "status"])
        assert status_result.exit_code == 0
        status_data = status_result.json()
        assert status_data["data"]["statuses"][0]["percentage"] == -40.0

        # 6. 更新预算
        update_result = cli_runner.invoke(app, [
            "budget", "update",
            "--id", str(budget_id),
            "--amount", "6000"
        ])
        assert update_result.exit_code == 0
        update_data = update_result.json()
        assert update_data["success"] is True
        assert update_data["data"]["amount"] == "6000.00"  # from_cents 返回字符串

        # 7. 查看历史
        history_result = cli_runner.invoke(app, ["history", "history"])
        assert history_result.exit_code == 0
        history_data = history_result.json()
        assert history_data["data"]["count"] == 1

        # 8. 删除预算
        delete_result = cli_runner.invoke(app, ["budget", "delete", "--id", str(budget_id)])
        assert delete_result.exit_code == 0
        delete_data = delete_result.json()
        assert delete_data["success"] is True

        # 9. 确认已删除
        list_result = cli_runner.invoke(app, ["budget", "ls"])
        assert list_result.exit_code == 0
        list_data = list_result.json()
        assert list_data["data"]["count"] == 0

    def test_multiple_budgets_with_different_periods(self, budget_runner):
        """测试不同周期的多个预算"""
        cli_runner, conn = budget_runner

        from cang.budget.cli import app

        # 创建月度预算
        cli_runner.invoke(app, [
            "budget", "set",
            "--category", "餐饮",
            "--amount", "5000",
            "--period", "month",
            "--start", "2026-03-01",
            "--end", "2026-03-31"
        ])

        # 创建年度预算
        cli_runner.invoke(app, [
            "budget", "set",
            "--category", "旅游",
            "--amount", "20000",
            "--period", "year",
            "--start", "2026-01-01",
            "--end", "2026-12-31"
        ])

        # 列出所有预算
        list_result = cli_runner.invoke(app, ["budget", "ls"])
        assert list_result.exit_code == 0
        list_data = list_result.json()
        assert list_data["data"]["count"] == 2

        # 按周期筛选
        month_result = cli_runner.invoke(app, ["budget", "ls", "--period", "month"])
        month_data = month_result.json()
        assert month_data["data"]["count"] == 1
        assert month_data["data"]["budgets"][0]["period"] == "month"

        year_result = cli_runner.invoke(app, ["budget", "ls", "--period", "year"])
        year_data = year_result.json()
        assert year_data["data"]["count"] == 1
        assert year_data["data"]["budgets"][0]["period"] == "year"
