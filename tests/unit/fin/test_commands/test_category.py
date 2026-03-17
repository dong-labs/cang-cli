"""Category 命令测试

测试 cang.fin.category 模块的所有命令。
"""

import sqlite3
import json

import pytest
from typer.testing import CliRunner

from cang.fin.commands.category import app


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def fin_db(memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """创建带有 fin 模块表结构的内存数据库"""
    # 创建 categories 表
    memory_db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
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
# Test list_categories_cmd
# ============================================================================

class TestListCategoriesCmd:
    """测试 cang fin category ls 命令"""

    def test_empty_list(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试空分类列表"""
        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["categories"] == []

    def test_list_single_category(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试列出单个分类"""
        fin_db.execute("INSERT INTO categories (name) VALUES (?)", ("餐饮",))
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert len(data["data"]["categories"]) == 1
        assert data["data"]["categories"][0]["name"] == "餐饮"

    def test_list_multiple_categories(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试列出多个分类"""
        for name in ["餐饮", "交通", "购物"]:
            fin_db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert len(data["data"]["categories"]) == 3

    def test_categories_order_by_id(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试分类按 ID 排序"""
        fin_db.execute("INSERT INTO categories (name) VALUES (?)", ("餐饮",))
        fin_db.execute("INSERT INTO categories (name) VALUES (?)", ("交通",))
        fin_db.commit()

        result = cli_runner.invoke(app, ["ls"])
        data = json.loads(result.stdout)

        categories = data["data"]["categories"]
        assert categories[0]["id"] < categories[1]["id"]


# ============================================================================
# Test add_category
# ============================================================================

class TestAddCategory:
    """测试 cang fin category add 命令"""

    def test_add_basic_category(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加基本分类"""
        result = cli_runner.invoke(app, ["add", "餐饮"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["category"]["name"] == "餐饮"
        assert "added" in data["data"]["message"].lower()

    def test_add_with_chinese_name(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加中文分类名称"""
        result = cli_runner.invoke(app, ["add", "交通"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["category"]["name"] == "交通"

    def test_add_duplicate_name_returns_error(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加重复分类名称返回错误"""
        # 第一次添加成功
        cli_runner.invoke(app, ["add", "重复"])

        # 第二次添加同名分类
        result = cli_runner.invoke(app, ["add", "重复"])
        assert result.exit_code == 0

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "ALREADY_EXISTS"

    def test_add_multiple_categories(self, fin_db: sqlite3.Connection, cli_runner: CliRunner):
        """测试添加多个不同分类"""
        categories = ["餐饮", "交通", "购物", "娱乐", "居住"]

        for cat in categories:
            result = cli_runner.invoke(app, ["add", cat])
            assert result.exit_code == 0
            data = json.loads(result.stdout)
            assert data["success"] is True

        # 验证所有分类都已添加
        result = cli_runner.invoke(app, ["ls"])
        data = json.loads(result.stdout)
        assert len(data["data"]["categories"]) == len(categories)
