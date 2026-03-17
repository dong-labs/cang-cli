"""Fin 模块 CLI 集成测试

测试完整的 CLI 命令流程，从用户角度验证功能正常工作。
"""

import json
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cang.fin.cli import app


# ============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def cli_runner() -> CliRunner:
    """创建 CLI 测试运行器"""
    return CliRunner()


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """创建临时数据库路径"""
    db_path = tmp_path / ".cang" / "cang.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Mock 数据库路径
    import cang.db.connection as conn_module
    # 清除 lru_cache
    conn_module.get_db_path.cache_clear()

    def mock_get_db_path() -> Path:
        return db_path

    monkeypatch.setattr(conn_module, "get_db_path", mock_get_db_path)

    # 重置连接
    conn_module.close_connection()

    return db_path


def parse_json_output(output: str) -> dict:
    """解析 JSON 输出"""
    return json.loads(output)


def assert_success(output: str) -> dict:
    """断言响应为成功格式"""
    data = parse_json_output(output)
    assert data["success"] is True, f"Expected success, got: {data}"
    assert "data" in data
    return data["data"]


def assert_error(output: str, expected_code: str | None = None) -> dict:
    """断言响应为错误格式"""
    data = parse_json_output(output)
    assert data["success"] is False, f"Expected error, got: {data}"
    assert "error" in data

    if expected_code:
        assert data["error"]["code"] == expected_code

    return data["error"]


# ============================================================================
# Init Command Tests
# ============================================================================

class TestFinInit:
    """测试 cang fin init 命令"""

    def test_init_creates_database(self, cli_runner: CliRunner, temp_db: Path):
        """测试初始化创建数据库文件"""
        result = cli_runner.invoke(app, ["init"])
        assert result.exit_code == 0

        data = assert_success(result.stdout)
        assert data["message"] == "Database initialized successfully"
        assert temp_db.exists()

    def test_init_twice(self, cli_runner: CliRunner, temp_db: Path):
        """测试重复初始化"""
        # 第一次初始化
        cli_runner.invoke(app, ["init"])

        # 第二次初始化
        result = cli_runner.invoke(app, ["init"])
        assert result.exit_code == 0

        data = assert_success(result.stdout)
        assert "already initialized" in data["message"].lower()

    def test_init_creates_default_categories(self, cli_runner: CliRunner, temp_db: Path):
        """测试初始化创建默认分类"""
        result = cli_runner.invoke(app, ["init"])
        data = assert_success(result.stdout)

        assert data["categories_count"] == 9
        assert "餐饮" in data["default_categories"]


# ============================================================================
# Account Workflow Tests
# ============================================================================

class TestAccountWorkflow:
    """测试账户管理完整流程"""

    def test_account_crud(self, cli_runner: CliRunner, temp_db: Path):
        """测试账户增删改查流程"""
        # 初始化数据库
        cli_runner.invoke(app, ["init"])

        # 1. 添加账户
        result = cli_runner.invoke(app, ["account", "add", "-n", "招商银行", "-t", "bank"])
        data = assert_success(result.stdout)
        account_id = data["id"]
        assert data["name"] == "招商银行"

        # 2. 列出账户
        result = cli_runner.invoke(app, ["account", "ls"])
        data = assert_success(result.stdout)
        assert len(data["accounts"]) == 1

        # 3. 获取账户详情
        result = cli_runner.invoke(app, ["account", "get", "--id", str(account_id)])
        data = assert_success(result.stdout)
        assert data["account"]["name"] == "招商银行"

        # 4. 查询余额（应为0）
        result = cli_runner.invoke(app, ["account", "balance", "--account-id", str(account_id)])
        data = assert_success(result.stdout)
        assert data["balance"] == "0.00"

    def test_add_multiple_accounts(self, cli_runner: CliRunner, temp_db: Path):
        """测试添加多个账户"""
        cli_runner.invoke(app, ["init"])

        accounts = [
            ("现金", "cash"),
            ("招商银行", "bank"),
            ("支付宝", "alipay"),
            ("微信", "wechat"),
            ("信用卡", "credit"),
        ]

        for name, acc_type in accounts:
            result = cli_runner.invoke(app, ["account", "add", "-n", name, "-t", acc_type])
            assert result.exit_code == 0

        # 验证所有账户都已创建
        result = cli_runner.invoke(app, ["account", "ls"])
        data = assert_success(result.stdout)
        assert len(data["accounts"]) == len(accounts)

    def test_duplicate_account_name(self, cli_runner: CliRunner, temp_db: Path):
        """测试重复账户名称"""
        cli_runner.invoke(app, ["init"])

        # 添加第一个账户
        cli_runner.invoke(app, ["account", "add", "-n", "重复", "-t", "bank"])

        # 添加同名账户
        result = cli_runner.invoke(app, ["account", "add", "-n", "重复", "-t", "cash"])
        assert_error(result.stdout, "ALREADY_EXISTS")

    def test_invalid_account_type(self, cli_runner: CliRunner, temp_db: Path):
        """测试无效账户类型"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "测试", "-t", "invalid"])
        assert_error(result.stdout, "INVALID_INPUT")


# ============================================================================
# Transaction Workflow Tests
# ============================================================================

class TestTransactionWorkflow:
    """测试交易管理完整流程"""

    def test_transaction_crud(self, cli_runner: CliRunner, temp_db: Path):
        """测试交易增删改查流程"""
        # 初始化
        cli_runner.invoke(app, ["init"])

        # 创建账户
        result = cli_runner.invoke(app, ["account", "add", "-n", "招商银行", "-t", "bank"])
        account_data = assert_success(result.stdout)
        account_id = account_data["id"]

        # 1. 添加交易
        result = cli_runner.invoke(app, [
            "tx", "add",
            "--amount", "-29.9",
            "--account", str(account_id),
            "--category", "餐饮",
            "--note", "午餐"
        ])
        data = assert_success(result.stdout)
        tx_id = data["transaction"]["id"]
        assert data["transaction"]["amount_cents"] == -2990

        # 2. 列出交易
        result = cli_runner.invoke(app, ["tx", "ls"])
        data = assert_success(result.stdout)
        assert len(data["transactions"]) == 1

        # 3. 获取交易详情
        result = cli_runner.invoke(app, ["tx", "get", "--id", str(tx_id)])
        data = assert_success(result.stdout)
        assert data["transaction"]["category"] == "餐饮"

        # 4. 更新交易
        result = cli_runner.invoke(app, [
            "tx", "update",
            "--id", str(tx_id),
            "--amount", "-39.9",
            "--note", "晚餐"
        ])
        data = assert_success(result.stdout)
        assert data["transaction"]["amount_cents"] == -3990
        assert data["transaction"]["note"] == "晚餐"

        # 5. 删除交易
        result = cli_runner.invoke(app, ["tx", "delete", "--id", str(tx_id)])
        assert_success(result.stdout)

        # 验证已删除
        result = cli_runner.invoke(app, ["tx", "get", "--id", str(tx_id)])
        assert_error(result.stdout, "NOT_FOUND")

    def test_transaction_with_income(self, cli_runner: CliRunner, temp_db: Path):
        """测试收入交易"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        account_data = assert_success(result.stdout)

        result = cli_runner.invoke(app, [
            "tx", "add",
            "--amount", "10000",
            "--account", str(account_data["id"]),
            "--category", "工资"
        ])
        data = assert_success(result.stdout)
        assert data["transaction"]["amount_cents"] == 1000000

    def test_transaction_filtering(self, cli_runner: CliRunner, temp_db: Path):
        """测试交易筛选"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        account_data = assert_success(result.stdout)
        account_id = account_data["id"]

        # 添加不同分类的交易
        cli_runner.invoke(app, ["tx", "add", "--amount", "-10", "--account", str(account_id), "--category", "餐饮"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-20", "--account", str(account_id), "--category", "交通"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-15", "--account", str(account_id), "--category", "餐饮"])

        # 按分类筛选
        result = cli_runner.invoke(app, ["tx", "ls", "--category", "餐饮"])
        data = assert_success(result.stdout)
        assert len(data["transactions"]) == 2

        # 限制数量
        result = cli_runner.invoke(app, ["tx", "ls", "--limit", "1"])
        data = assert_success(result.stdout)
        assert data["count"] == 1
        assert data["total"] == 3

    def test_transaction_with_nonexistent_account(self, cli_runner: CliRunner, temp_db: Path):
        """测试添加到不存在的账户"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, [
            "tx", "add",
            "--amount", "-10",
            "--account", "999"
        ])
        assert_error(result.stdout, "NOT_FOUND")


# ============================================================================
# Balance Calculation Tests
# ============================================================================

class TestBalanceCalculation:
    """测试余额计算"""

    def test_single_account_balance(self, cli_runner: CliRunner, temp_db: Path):
        """测试单个账户余额"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        account_data = assert_success(result.stdout)
        account_id = account_data["id"]

        # 添加收入
        cli_runner.invoke(app, ["tx", "add", "--amount", "100", "--account", str(account_id), "--category", "工资"])
        # 添加支出
        cli_runner.invoke(app, ["tx", "add", "--amount", "-29.9", "--account", str(account_id), "--category", "餐饮"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-50", "--account", str(account_id), "--category", "交通"])

        # 查询余额
        result = cli_runner.invoke(app, ["account", "balance", "--account-id", str(account_id)])
        data = assert_success(result.stdout)
        assert data["balance"] == "20.10"  # 100 - 29.9 - 50

    def test_all_accounts_balance(self, cli_runner: CliRunner, temp_db: Path):
        """测试所有账户余额"""
        cli_runner.invoke(app, ["init"])

        # 创建两个账户
        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        acc1 = assert_success(result.stdout)
        result = cli_runner.invoke(app, ["account", "add", "-n", "现金", "-t", "cash"])
        acc2 = assert_success(result.stdout)

        # 添加交易
        cli_runner.invoke(app, ["tx", "add", "--amount", "100", "--account", str(acc1["id"])])
        cli_runner.invoke(app, ["tx", "add", "--amount", "50", "--account", str(acc2["id"])])

        # 查询所有余额
        result = cli_runner.invoke(app, ["account", "balance"])
        data = assert_success(result.stdout)
        assert len(data["balances"]) == 2


# ============================================================================
# Transfer Workflow Tests
# ============================================================================

class TestTransferWorkflow:
    """测试转账流程"""

    def test_basic_transfer(self, cli_runner: CliRunner, temp_db: Path):
        """测试基本转账"""
        cli_runner.invoke(app, ["init"])

        # 创建两个账户
        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        acc1 = assert_success(result.stdout)
        result = cli_runner.invoke(app, ["account", "add", "-n", "现金", "-t", "cash"])
        acc2 = assert_success(result.stdout)

        # 转账
        result = cli_runner.invoke(app, [
            "transfer", "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100"
        ])
        data = assert_success(result.stdout)
        assert data["amount"] == "100.00"
        assert data["fee"] == "0.00"

        # 验证转账记录
        result = cli_runner.invoke(app, ["transfer", "ls"])
        data = assert_success(result.stdout)
        assert data["count"] == 1

        # 验证创建了交易记录
        result = cli_runner.invoke(app, ["tx", "ls"])
        data = assert_success(result.stdout)
        assert len(data["transactions"]) == 2  # 转出 + 转入

    def test_transfer_with_fee(self, cli_runner: CliRunner, temp_db: Path):
        """测试带手续费的转账"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        acc1 = assert_success(result.stdout)
        result = cli_runner.invoke(app, ["account", "add", "-n", "现金", "-t", "cash"])
        acc2 = assert_success(result.stdout)

        result = cli_runner.invoke(app, [
            "transfer", "transfer",
            "--from", str(acc1["id"]),
            "--to", str(acc2["id"]),
            "--amount", "100",
            "--fee", "2.5"
        ])
        data = assert_success(result.stdout)
        assert data["total_deducted"] == "102.50"

    def test_transfer_to_same_account(self, cli_runner: CliRunner, temp_db: Path):
        """测试转账到同一账户"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        acc = assert_success(result.stdout)

        result = cli_runner.invoke(app, [
            "transfer", "transfer",
            "--from", str(acc["id"]),
            "--to", str(acc["id"]),
            "--amount", "100"
        ])
        assert_error(result.stdout, "INVALID_INPUT")


# ============================================================================
# Summary Tests
# ============================================================================

class TestSummary:
    """测试交易汇总"""

    def test_monthly_summary(self, cli_runner: CliRunner, temp_db: Path):
        """测试月度汇总"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        acc = assert_success(result.stdout)

        # 添加本月的交易
        today = date.today().isoformat()
        cli_runner.invoke(app, ["tx", "add", "--amount", "10000", "--account", str(acc["id"]), "--date", today, "--category", "工资"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-29.90", "--account", str(acc["id"]), "--date", today, "--category", "餐饮"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-50", "--account", str(acc["id"]), "--date", today, "--category", "购物"])

        # 查询月度汇总
        result = cli_runner.invoke(app, ["tx", "summary", "--period", "month"])
        data = assert_success(result.stdout)
        assert data["income"] == "10000.00"
        assert data["expense"] == "79.90"
        assert data["net"] == "9920.10"
        assert data["transaction_count"] == 3

    def test_summary_with_date_range(self, cli_runner: CliRunner, temp_db: Path):
        """测试自定义日期范围汇总"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["account", "add", "-n", "银行", "-t", "bank"])
        acc = assert_success(result.stdout)

        # 添加不同日期的交易
        cli_runner.invoke(app, ["tx", "add", "--amount", "-100", "--account", str(acc["id"]), "--date", "2026-03-10"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-200", "--account", str(acc["id"]), "--date", "2026-03-15"])
        cli_runner.invoke(app, ["tx", "add", "--amount", "-300", "--account", str(acc["id"]), "--date", "2026-03-20"])

        # 查询指定范围
        result = cli_runner.invoke(app, [
            "tx", "summary",
            "--start", "2026-03-12",
            "--end", "2026-03-18"
        ])
        data = assert_success(result.stdout)
        assert data["expense_cents"] == 20000
        assert data["transaction_count"] == 1


# ============================================================================
# Category Tests
# ============================================================================

class TestCategoryWorkflow:
    """测试分类管理"""

    def test_list_categories(self, cli_runner: CliRunner, temp_db: Path):
        """测试列出分类"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["category", "ls"])
        data = assert_success(result.stdout)
        assert len(data["categories"]) == 9  # 默认分类数量
        category_names = [c["name"] for c in data["categories"]]
        assert "餐饮" in category_names
        assert "交通" in category_names

    def test_add_custom_category(self, cli_runner: CliRunner, temp_db: Path):
        """测试添加自定义分类"""
        cli_runner.invoke(app, ["init"])

        result = cli_runner.invoke(app, ["category", "add", "投资"])
        data = assert_success(result.stdout)
        assert data["category"]["name"] == "投资"

        # 验证分类已添加
        result = cli_runner.invoke(app, ["category", "ls"])
        data = assert_success(result.stdout)
        category_names = [c["name"] for c in data["categories"]]
        assert "投资" in category_names

    def test_duplicate_category(self, cli_runner: CliRunner, temp_db: Path):
        """测试重复分类名称"""
        cli_runner.invoke(app, ["init"])

        # "餐饮" 是默认分类
        result = cli_runner.invoke(app, ["category", "add", "餐饮"])
        assert_error(result.stdout, "ALREADY_EXISTS")


# ============================================================================
# Schema Tests
# ============================================================================

class TestSchemaCommand:
    """测试 schema 命令"""

    def test_db_schema(self, cli_runner: CliRunner, temp_db: Path):
        """测试查看数据库结构"""
        result = cli_runner.invoke(app, ["db-schema"])
        data = assert_success(result.stdout)

        assert "schema" in data
        assert "accounts" in data["schema"]
        assert "transactions" in data["schema"]
        assert "categories" in data["schema"]
        assert "transfers" in data["schema"]

        # 验证字段
        assert "columns" in data["schema"]["accounts"]
        assert "id" in data["schema"]["accounts"]["columns"]
        assert "name" in data["schema"]["accounts"]["columns"]
