"""测试数据库 Schema 管理模块

测试 cang.db.schema 模块的所有函数:
- get_schema_version()
- set_schema_version()
- init_database()
- is_initialized()
- 各个 _create_*_table() 函数
"""

from unittest.mock import patch

import pytest

from cang.db import schema
from cang.db.connection import close_connection


# =============================================================================
# get_schema_version() 测试
# =============================================================================

class TestGetSchemaVersion:
    """测试 get_schema_version 函数"""

    def setup_method(self):
        """每个测试前关闭连接，使用测试数据库"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_none_when_not_initialized(self, memory_db):
        """数据库未初始化时返回 None"""
        # 注意：由于使用内存数据库，需要 mock get_connection
        # 这里我们使用真实的连接但手动控制
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            # 模拟游标返回 None（数据库中无记录）
            mock_cursor = mock_get_cursor.return_value.__enter__.return_value
            mock_cursor.fetchone.return_value = None

            version = schema.get_schema_version()
            assert version is None

    def test_returns_version_string(self, memory_db_with_schema):
        """数据库已初始化时返回版本号"""
        # 先设置版本
        memory_db_with_schema.execute(
            "INSERT INTO cang_meta (key, value) VALUES ('schema_version', '1')"
        )
        memory_db_with_schema.commit()

        # 使用 mock 来测试
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = mock_get_cursor.return_value.__enter__.return_value
            mock_cursor.fetchone.return_value = {"value": "1"}

            version = schema.get_schema_version()
            assert version == "1"


# =============================================================================
# set_schema_version() 测试
# =============================================================================

class TestSetSchemaVersion:
    """测试 set_schema_version 函数"""

    def setup_method(self):
        """每个测试前关闭连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_sets_version(self, memory_db_with_schema):
        """测试设置版本号"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = mock_get_cursor.return_value.__enter__.return_value
            schema.set_schema_version("1")
            mock_cursor.execute.assert_called_once()

    def test_overwrites_existing_version(self, memory_db_with_schema):
        """测试覆盖已有版本"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = mock_get_cursor.return_value.__enter__.return_value
            schema.set_schema_version("1")
            schema.set_schema_version("2")
            # 应该调用两次，第二次使用 INSERT OR REPLACE
            assert mock_cursor.execute.call_count == 2


# =============================================================================
# _create_*_table() 测试
# =============================================================================

class TestCreateTables:
    """测试各个表创建函数"""

    def setup_method(self):
        """每个测试前关闭连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_create_meta_table(self, memory_db):
        """测试创建 cang_meta 表"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_meta_table()
            # 验证表已创建
            cursor = memory_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='cang_meta'"
            )
            assert cursor.fetchone() is not None

    def test_meta_table_structure(self, memory_db):
        """测试 cang_meta 表结构"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_meta_table()
            # 验证表结构
            cursor = memory_db.execute("PRAGMA table_info(cang_meta)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            assert columns == {"key": "TEXT", "value": "TEXT"}

    def test_create_accounts_table(self, memory_db):
        """测试创建 accounts 表"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_accounts_table()
            cursor = memory_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'"
            )
            assert cursor.fetchone() is not None

    def test_accounts_table_structure(self, memory_db):
        """测试 accounts 表结构"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_accounts_table()
            cursor = memory_db.execute("PRAGMA table_info(accounts)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            assert "id" in columns
            assert "name" in columns
            assert "type" in columns
            assert "currency" in columns

    def test_create_transactions_table(self, memory_db):
        """测试创建 transactions 表"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_transactions_table()
            cursor = memory_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
            )
            assert cursor.fetchone() is not None

    def test_transactions_table_structure(self, memory_db):
        """测试 transactions 表结构"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_transactions_table()
            cursor = memory_db.execute("PRAGMA table_info(transactions)")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            assert "id" in columns
            assert "date" in columns
            assert "amount_cents" in columns
            assert "account_id" in columns

    def test_create_categories_table(self, memory_db):
        """测试创建 categories 表"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_categories_table()
            cursor = memory_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
            )
            assert cursor.fetchone() is not None

    def test_create_transfers_table(self, memory_db):
        """测试创建 transfers 表"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            schema._create_transfers_table()
            cursor = memory_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='transfers'"
            )
            assert cursor.fetchone() is not None


# =============================================================================
# init_database() 测试
# =============================================================================

class TestInitDatabase:
    """测试 init_database 函数"""

    def setup_method(self):
        """每个测试前关闭连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_creates_all_tables_on_fresh_install(self, memory_db):
        """测试全新安装时创建所有表"""
        # Mock get_cursor 使用我们的内存数据库
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            # Mock get_schema_version 返回 None（全新安装）
            with patch("cang.db.schema.get_schema_version", return_value=None):
                schema.init_database()

            # 验证所有表都已创建
            tables = ["cang_meta", "accounts", "transactions", "categories", "transfers"]
            for table in tables:
                cursor = memory_db.execute(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                )
                assert cursor.fetchone() is not None, f"Table {table} not created"

    def test_sets_schema_version_on_fresh_install(self, memory_db):
        """测试全新安装时设置 schema 版本"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            with patch("cang.db.schema.get_schema_version", return_value=None):
                schema.init_database()

            # 验证版本号已设置
            cursor = memory_db.execute(
                "SELECT value FROM cang_meta WHERE key = 'schema_version'"
            )
            result = cursor.fetchone()
            assert result is not None
            assert result["value"] == schema.SCHEMA_VERSION

    def test_raises_on_version_mismatch(self, memory_db_with_schema):
        """测试版本不匹配时抛出异常"""
        # 设置一个不同的版本
        memory_db_with_schema.execute(
            "INSERT INTO cang_meta (key, value) VALUES ('schema_version', '999')"
        )
        memory_db_with_schema.commit()

        with patch("cang.db.schema.get_schema_version", return_value="999"):
            with pytest.raises(ValueError, match="Database version mismatch"):
                schema.init_database()

    def test_idempotent_when_already_initialized(self, memory_db_with_schema):
        """测试已初始化时重复调用是幂等的"""
        # 设置正确的版本
        memory_db_with_schema.execute(
            "INSERT INTO cang_meta (key, value) VALUES ('schema_version', ?)",
            (schema.SCHEMA_VERSION,)
        )
        memory_db_with_schema.commit()

        with patch("cang.db.schema.get_schema_version", return_value=schema.SCHEMA_VERSION):
            # 不应抛出异常
            schema.init_database()


# =============================================================================
# is_initialized() 测试
# =============================================================================

class TestIsInitialized:
    """测试 is_initialized 函数"""

    def setup_method(self):
        """每个测试前关闭连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_returns_false_when_not_initialized(self):
        """测试未初始化时返回 False"""
        with patch("cang.db.schema.get_schema_version", return_value=None):
            assert schema.is_initialized() is False

    def test_returns_true_when_initialized(self):
        """测试已初始化时返回 True"""
        with patch("cang.db.schema.get_schema_version", return_value="1"):
            assert schema.is_initialized() is True


# =============================================================================
# 集成测试
# =============================================================================

class TestSchemaIntegration:
    """Schema 管理集成测试"""

    def setup_method(self):
        """每个测试前关闭连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_full_initialization_workflow(self, memory_db):
        """测试完整的初始化工作流"""
        # Mock get_cursor 使用内存数据库
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            with patch("cang.db.schema.get_schema_version") as mock_get_version:
                # 第一次调用返回 None（未初始化）
                mock_get_version.return_value = None

                # 初始化数据库
                schema.init_database()

                # 之后调用返回版本号
                mock_get_version.return_value = schema.SCHEMA_VERSION

                # 验证已初始化
                assert schema.is_initialized() is True
                assert schema.get_schema_version() == schema.SCHEMA_VERSION

    def test_tables_are_idempotent(self, memory_db):
        """测试重复创建表是安全的（CREATE IF NOT EXISTS）"""
        with patch("cang.db.schema.get_cursor") as mock_get_cursor:
            mock_cursor = memory_db.cursor()
            mock_get_cursor.return_value.__enter__.return_value = mock_cursor

            # 多次创建表不应报错
            schema._create_meta_table()
            schema._create_meta_table()
            schema._create_accounts_table()
            schema._create_accounts_table()

            # 表应该存在
            cursor = memory_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('cang_meta', 'accounts')"
            )
            results = cursor.fetchall()
            assert len(results) == 2
