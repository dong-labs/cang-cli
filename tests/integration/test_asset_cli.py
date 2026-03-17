"""Asset 模块 CLI 集成测试

测试 cang asset 命令行接口的所有子命令:
- asset init: 初始化模块
- asset ls: 列出资产
- asset add: 添加资产
- asset get: 获取资产详情
- asset update: 更新资产
- asset delete: 删除资产
- asset networth: 计算净资产
- asset schema: 显示表结构
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import sqlite3
from typer.testing import CliRunner

from cang.asset.cli import app
from cang.db.connection import close_connection


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def asset_db(tmp_path):
    """创建独立的测试数据库文件"""
    db_path = tmp_path / "test_asset.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    # 创建所有必要的表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cang_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.execute("""
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
    conn.execute(
        "INSERT INTO cang_meta (key, value) VALUES ('schema_version', '1')"
    )
    conn.commit()

    yield conn, db_path

    conn.close()


@pytest.fixture
def asset_runner(asset_db, cli_runner, monkeypatch):
    """配置使用测试数据库的 CLI 运行器"""
    conn, db_path = asset_db

    # Mock get_db_path 返回测试数据库路径
    def mock_get_db_path():
        return db_path

    # Mock get_cursor 返回测试数据库的 cursor (使用上下文管理器)
    from contextlib import contextmanager

    @contextmanager
    def mock_get_cursor():
        yield conn.cursor()

    # Patch 数据库连接相关
    monkeypatch.setattr("cang.db.connection.get_db_path", mock_get_db_path)
    monkeypatch.setattr("cang.db.connection.get_cursor", mock_get_cursor)
    monkeypatch.setattr("cang.asset.repository.get_cursor", mock_get_cursor)
    monkeypatch.setattr("cang.db.schema.get_cursor", mock_get_cursor)

    return cli_runner, conn


def run_command(runner, *args):
    """运行命令并返回解析后的 JSON 数据"""
    result = runner.invoke(app, args)
    # 如果有多个 JSON 对象，取最后一个成功的
    data = {}
    if result.stdout.strip():
        # 尝试按 }{ 或 }\n{ 分割多个 JSON 对象
        output = result.stdout.strip()
        # 分割多个 JSON 对象
        parts = output.replace('}\n{', '}|||{').replace('}{', '}|||{').split('|||')
        for obj_str in parts:
            try:
                data = json.loads(obj_str)
                # 如果找到一个成功的响应，就使用它
                if data.get("success") is True:
                    break
            except json.JSONDecodeError:
                pass
    return result.exit_code, result.stdout, data


def assert_success(data):
    """断言为成功响应"""
    assert data.get("success") is True, f"Expected success=True, got: {data}"
    assert "data" in data, f"Missing 'data' field in: {data}"
    return data["data"]


def assert_error(data, expected_code=None):
    """断言为错误响应"""
    assert data.get("success") is False, f"Expected success=False, got: {data}"
    assert "error" in data, f"Missing 'error' field in: {data}"
    if expected_code:
        assert data["error"]["code"] == expected_code
    return data["error"]


# =============================================================================
# asset init 命令测试
# =============================================================================

class TestAssetInit:
    """测试 asset init 命令"""

    def test_init_already_initialized(self, asset_runner):
        """测试数据库已初始化时的行为"""
        runner, conn = asset_runner

        # init 是一个子应用，下面有 init-asset 命令
        exit_code, output, data = run_command(runner, "init", "init-asset")

        assert exit_code == 0
        result = assert_success(data)


# =============================================================================
# asset ls 命令测试
# =============================================================================

class TestAssetLs:
    """测试 asset ls 命令"""

    def test_ls_empty(self, asset_runner):
        """测试空资产列表"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(runner, "ls")

        assert exit_code == 0
        result = assert_success(data)
        assert result["assets"] == []
        assert result["count"] == 0

    def test_ls_with_assets(self, asset_runner):
        """测试列出所有资产"""
        runner, conn = asset_runner

        # 插入测试数据
        conn.execute(
            "INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
            ("现金", "cash", 10000)
        )
        conn.execute(
            "INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
            ("招商银行", "bank", 500000)
        )
        conn.commit()

        exit_code, output, data = run_command(runner, "ls")

        assert exit_code == 0
        result = assert_success(data)
        assert result["count"] == 2
        assert len(result["assets"]) == 2

    def test_ls_filter_by_type(self, asset_runner):
        """测试按类型筛选"""
        runner, conn = asset_runner

        conn.execute("INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
                     ("现金", "cash", 10000))
        conn.execute("INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
                     ("Apple 股票", "stock", 800000))
        conn.commit()

        exit_code, output, data = run_command(runner, "ls", "--type", "stock")

        assert exit_code == 0
        result = assert_success(data)
        assert result["count"] == 1
        assert result["assets"][0]["type"] == "stock"

    def test_ls_filter_by_currency(self, asset_runner):
        """测试按货币筛选"""
        runner, conn = asset_runner

        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("现金", "cash", 10000, "CNY"))
        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("Apple 股票", "stock", 800000, "USD"))
        conn.commit()

        exit_code, output, data = run_command(runner, "ls", "--currency", "USD")

        assert exit_code == 0
        result = assert_success(data)
        assert result["count"] == 1
        assert result["assets"][0]["currency"] == "USD"

    def test_ls_invalid_type(self, asset_runner):
        """测试无效类型返回错误"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(runner, "ls", "--type", "invalid")

        # @json_output 会返回 JSON 格式的错误，所以 exit_code 仍然是 0
        assert exit_code == 0
        assert_error(data)


# =============================================================================
# asset add 命令测试
# =============================================================================

class TestAssetAdd:
    """测试 asset add 命令"""

    def test_add_with_value(self, asset_runner):
        """测试使用 value 添加资产"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "add",
            "--name", "现金",
            "--type", "cash",
            "--value", "100.50"
        )

        assert exit_code == 0
        result = assert_success(data)
        assert "asset" in result
        assert result["asset"]["value_cents"] == 10050

    def test_add_with_amount(self, asset_runner):
        """测试使用 amount 添加资产"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "add",
            "--name", "Apple 股票",
            "--type", "stock",
            "--amount", "150",
            "--code", "AAPL"
        )

        assert exit_code == 0
        result = assert_success(data)
        asset = result["asset"]
        assert asset["amount_cents"] == 15000
        assert asset["code"] == "AAPL"

    def test_add_with_all_params(self, asset_runner):
        """测试使用所有参数添加资产"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "add",
            "--name", "Apple 股票",
            "--type", "stock",
            "--amount", "150",
            "--currency", "USD",
            "--code", "AAPL",
            "--value", "25000"
        )

        assert exit_code == 0
        result = assert_success(data)
        asset = result["asset"]
        # 当同时指定 amount 和 value 时，只使用 value，amount 为 None
        assert asset["amount_cents"] is None
        assert asset["value_cents"] == 2500000
        assert asset["currency"] == "USD"

    def test_add_default_currency(self, asset_runner):
        """测试默认货币为 CNY"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "add",
            "--name", "现金",
            "--type", "cash",
            "--value", "100"
        )

        assert exit_code == 0
        result = assert_success(data)
        assert result["asset"]["currency"] == "CNY"

    def test_add_invalid_type(self, asset_runner):
        """测试无效类型返回错误"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "add",
            "--name", "测试",
            "--type", "invalid_type",
            "--value", "100"
        )

        # @json_output 会返回 JSON 格式的错误
        assert exit_code == 0
        assert_error(data)

    def test_add_missing_params(self, asset_runner):
        """测试缺少参数返回错误"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "add",
            "--name", "测试",
            "--type", "cash"
        )

        # @json_output 会返回 JSON 格式的错误
        assert exit_code == 0
        assert_error(data)

    def test_add_all_asset_types(self, asset_runner):
        """测试所有资产类型都可以添加"""
        runner, conn = asset_runner

        asset_types = [
            ("cash", "现金"),
            ("bank", "招商银行"),
            ("stock", "股票"),
            ("fund", "基金"),
            ("bond", "债券"),
            ("crypto", "比特币"),
            ("real_estate", "房产"),
            ("vehicle", "车辆"),
            ("gold", "黄金"),
            ("other", "其他"),
        ]

        for asset_type, name in asset_types:
            exit_code, _, data = run_command(
                runner, "add",
                "--name", name,
                "--type", asset_type,
                "--value", "100"
            )
            assert exit_code == 0, f"Failed to add asset type: {asset_type}"
            assert_success(data)


# =============================================================================
# asset get 命令测试
# =============================================================================

class TestAssetGet:
    """测试 asset get 命令"""

    def test_get_existing_asset(self, asset_runner):
        """测试获取存在的资产"""
        runner, conn = asset_runner

        # 先插入数据
        conn.execute(
            "INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
            ("现金", "cash", 10050)
        )
        conn.commit()

        exit_code, output, data = run_command(runner, "get", "--id", "1")

        assert exit_code == 0
        result = assert_success(data)
        assert result["asset"]["name"] == "现金"
        assert result["asset"]["value_cents"] == 10050
        assert "value_formatted" in result["asset"]

    def test_get_nonexistent_asset(self, asset_runner):
        """测试获取不存在的资产返回错误"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(runner, "get", "--id", "999")

        # @json_output 会返回 JSON 格式的错误
        assert exit_code == 0
        assert_error(data)


# =============================================================================
# asset update 命令测试
# =============================================================================

class TestAssetUpdate:
    """测试 asset update 命令"""

    def test_update_amount(self, asset_runner):
        """测试更新 amount"""
        runner, conn = asset_runner

        # 先创建资产
        conn.execute(
            "INSERT INTO assets (name, type, amount_cents, value_cents) VALUES (?, ?, ?, ?)",
            ("现金", "cash", 1000, 1000)
        )
        conn.commit()

        exit_code, output, data = run_command(
            runner, "update",
            "--id", "1",
            "--amount", "150"
        )

        assert exit_code == 0
        result = assert_success(data)
        assert result["asset"]["amount_cents"] == 15000

    def test_update_value(self, asset_runner):
        """测试更新 value"""
        runner, conn = asset_runner

        conn.execute(
            "INSERT INTO assets (name, type, amount_cents, value_cents) VALUES (?, ?, ?, ?)",
            ("Apple 股票", "stock", 15000, 250000)
        )
        conn.commit()

        exit_code, output, data = run_command(
            runner, "update",
            "--id", "1",
            "--value", "300"
        )

        assert exit_code == 0
        result = assert_success(data)
        assert result["asset"]["value_cents"] == 30000

    def test_update_both(self, asset_runner):
        """测试同时更新 amount 和 value"""
        runner, conn = asset_runner

        conn.execute(
            "INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
            ("基金", "fund", 10000)
        )
        conn.commit()

        exit_code, output, data = run_command(
            runner, "update",
            "--id", "1",
            "--amount", "150",
            "--value", "150"
        )

        assert exit_code == 0
        result = assert_success(data)
        assert result["asset"]["amount_cents"] == 15000
        assert result["asset"]["value_cents"] == 15000

    def test_update_nonexistent_asset(self, asset_runner):
        """测试更新不存在的资产返回错误"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "update",
            "--id", "999",
            "--value", "100"
        )

        # @json_output 会返回 JSON 格式的错误
        assert exit_code == 0
        assert_error(data)

    def test_update_without_params(self, asset_runner):
        """测试不传更新参数返回错误"""
        runner, conn = asset_runner

        conn.execute(
            "INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
            ("现金", "cash", 10000)
        )
        conn.commit()

        exit_code, output, data = run_command(
            runner, "update",
            "--id", "1"
        )

        # @json_output 会返回 JSON 格式的错误
        assert exit_code == 0
        assert_error(data)


# =============================================================================
# asset delete 命令测试
# =============================================================================

class TestAssetDelete:
    """测试 asset delete 命令"""

    def test_delete_existing_asset(self, asset_runner):
        """测试删除存在的资产"""
        runner, conn = asset_runner

        conn.execute(
            "INSERT INTO assets (name, type, value_cents) VALUES (?, ?, ?)",
            ("待删除", "cash", 10000)
        )
        conn.commit()

        exit_code, output, data = run_command(
            runner, "delete",
            "--id", "1"
        )

        assert exit_code == 0
        result = assert_success(data)
        assert result["deleted"] is True

        # 验证已删除
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE id = 1")
        assert cursor.fetchone() is None

    def test_delete_nonexistent_asset(self, asset_runner):
        """测试删除不存在的资产返回错误"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(
            runner, "delete",
            "--id", "999"
        )

        # @json_output 会返回 JSON 格式的错误
        assert exit_code == 0
        assert_error(data)


# =============================================================================
# asset networth 命令测试
# =============================================================================

class TestAssetNetworth:
    """测试 asset networth 命令"""

    def test_networth_empty(self, asset_runner):
        """测试空数据库的净资产"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(runner, "networth")

        assert exit_code == 0
        result = assert_success(data)
        # networth 可能是字符串或浮点数
        assert float(result["networth"]) == 0.0
        assert result["asset_count"] == 0

    def test_networth_single_currency(self, asset_runner):
        """测试单一货币净资产"""
        runner, conn = asset_runner

        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("现金", "cash", 10000, "CNY"))
        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("招商银行", "bank", 500000, "CNY"))
        conn.commit()

        exit_code, output, data = run_command(runner, "networth")

        assert exit_code == 0
        result = assert_success(data)
        assert result["networth_cents"] == 510000
        assert result["asset_count"] == 2

    def test_networth_multi_currency(self, asset_runner):
        """测试多货币净资产"""
        runner, conn = asset_runner

        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("现金", "cash", 10000, "CNY"))
        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("Apple 股票", "stock", 800000, "USD"))
        conn.execute("INSERT INTO assets (name, type, value_cents, currency) VALUES (?, ?, ?, ?)",
                     ("Tesla 股票", "stock", 500000, "USD"))
        conn.commit()

        exit_code, output, data = run_command(runner, "networth")

        assert exit_code == 0
        result = assert_success(data)
        assert result["asset_count"] == 3
        assert "CNY" in result["by_currency"]
        assert "USD" in result["by_currency"]


# =============================================================================
# asset schema 命令测试
# =============================================================================

class TestAssetSchema:
    """测试 asset schema 命令"""

    def test_schema(self, asset_runner):
        """测试返回 schema"""
        runner, conn = asset_runner

        exit_code, output, data = run_command(runner, "schema")

        assert exit_code == 0
        result = assert_success(data)
        assert "schema" in result
        assert "assets" in result["schema"]
        assert "columns" in result["schema"]["assets"]
        assert "asset_types" in result["schema"]["assets"]
