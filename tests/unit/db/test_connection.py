"""测试数据库连接管理模块

测试 cang.db.connection 模块的所有函数:
- get_db_path()
- get_connection()
- close_connection()
- get_cursor()
"""

import sqlite3
import threading
from pathlib import Path
from unittest.mock import patch

import pytest

from cang.db.connection import (
    get_db_path,
    get_connection,
    close_connection,
    get_cursor,
    _connection,
    _lock,
)


# =============================================================================
# get_db_path() 测试
# =============================================================================

class TestGetDbPath:
    """测试 get_db_path 函数"""

    def test_returns_path_object(self):
        """应该返回 Path 对象"""
        path = get_db_path()
        assert isinstance(path, Path)

    def test_path_ends_with_cang_db(self):
        """路径应该以 ~/.cang/cang.db 结尾"""
        path = get_db_path()
        assert path.name == "cang.db"
        assert path.parent.name == ".cang"

    def test_path_is_absolute(self):
        """路径应该是绝对路径"""
        path = get_db_path()
        assert path.is_absolute()

    def test_directory_exists(self):
        """父目录应该存在（函数会自动创建）"""
        path = get_db_path()
        assert path.parent.exists()

    def test_caching(self):
        """应该使用缓存，多次调用返回相同对象"""
        path1 = get_db_path()
        path2 = get_db_path()
        # lru_cache 确保返回相同对象
        assert path1 is path2

    def test_home_directory(self):
        """应该位于用户主目录下"""
        path = get_db_path()
        home = Path.home()
        # 检查路径是否在 home 目录下
        assert path.is_relative_to(home) or str(path).startswith(str(home))


# =============================================================================
# get_connection() 测试
# =============================================================================

class TestGetConnection:
    """测试 get_connection 函数"""

    def setup_method(self):
        """每个测试前关闭已有连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_returns_connection(self):
        """应该返回 SQLite 连接对象"""
        conn = get_connection()
        assert isinstance(conn, sqlite3.Connection)

    def test_row_factory_set(self):
        """连接应该设置 row_factory 为 sqlite3.Row"""
        conn = get_connection()
        assert conn.row_factory is sqlite3.Row

    def test_singleton_pattern(self):
        """应该使用单例模式，多次调用返回同一连接"""
        conn1 = get_connection()
        conn2 = get_connection()
        assert conn1 is conn2

    def test_database_file_created(self):
        """数据库文件应该被创建"""
        conn = get_connection()
        db_path = get_db_path()
        assert db_path.exists()

    def test_can_execute_query(self):
        """连接应该能够执行查询"""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1


class TestGetConnectionThreadSafety:
    """测试 get_connection 的线程安全性"""

    def setup_method(self):
        """每个测试前关闭已有连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_concurrent_calls(self):
        """多线程并发调用应该是安全的"""
        connections = []
        errors = []

        def get_conn():
            try:
                conn = get_connection()
                connections.append(conn)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=get_conn)
            for _ in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(connections) == 10
        # 所有连接应该是同一个对象
        assert all(conn is connections[0] for conn in connections)


# =============================================================================
# close_connection() 测试
# =============================================================================

class TestCloseConnection:
    """测试 close_connection 函数"""

    def test_closes_open_connection(self):
        """应该关闭打开的连接"""
        conn = get_connection()
        close_connection()
        # 验证连接已关闭
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")

    def test_idempotent(self):
        """多次调用应该是安全的（幂等）"""
        get_connection()
        close_connection()
        close_connection()  # 不应抛出异常

    def test_reopen_after_close(self):
        """关闭后应该能够重新获取连接"""
        get_connection()
        close_connection()

        conn = get_connection()
        assert isinstance(conn, sqlite3.Connection)
        # 新连接应该可以正常使用
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1


# =============================================================================
# get_cursor() 测试
# =============================================================================

class TestGetCursor:
    """测试 get_cursor 上下文管理器"""

    def setup_method(self):
        """每个测试前关闭已有连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_yields_cursor(self):
        """应该 yield 一个游标对象"""
        with get_cursor() as cur:
            assert isinstance(cur, sqlite3.Cursor)

    def test_can_execute_query(self):
        """游标应该能够执行查询"""
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result[0] == 1

    def test_auto_commit_on_success(self):
        """成功时应该自动提交"""
        # 创建测试表
        with get_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
            """)
            cur.execute("INSERT INTO test_table (value) VALUES (?)", ("test",))

        # 验证数据已提交
        with get_cursor() as cur:
            cur.execute("SELECT value FROM test_table WHERE id = 1")
            result = cur.fetchone()
            assert result is not None
            assert result["value"] == "test"

    def test_auto_rollback_on_error(self):
        """出错时应该自动回滚"""
        # 先创建表
        with get_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    value TEXT
                )
            """)
        # 清空表
        with get_cursor() as cur:
            cur.execute("DELETE FROM test_table")

        # 测试场景：在同一个上下文中，第一条语句成功，第二条语句失败
        # 预期：整个事务应该被回滚
        conn = get_connection()
        # 显式开始事务（防止自动提交）
        conn.execute("BEGIN")

        with pytest.raises(sqlite3.IntegrityError):
            with get_cursor() as cur:
                # 这两条语句在显式事务中
                cur.execute("INSERT INTO test_table (id, value) VALUES (1, 'first')")
                # 主键冲突
                cur.execute("INSERT INTO test_table (id, value) VALUES (1, 'duplicate')")

        # rollback 被调用后，验证第一行也被回滚了
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM test_table")
            result = cur.fetchone()
            assert result["count"] == 0, "Transaction should have been rolled back"

    def test_cursor_closed_on_exit(self):
        """退出上下文时游标应该被关闭"""
        with get_cursor() as cur:
            cursor_id = id(cur)

        # 游标已关闭，再次使用应该抛出异常
        with pytest.raises(sqlite3.ProgrammingError):
            cur.execute("SELECT 1")


# =============================================================================
# 集成测试
# =============================================================================

class TestConnectionIntegration:
    """连接管理集成测试"""

    def setup_method(self):
        """每个测试前关闭已有连接"""
        close_connection()

    def teardown_method(self):
        """每个测试后清理"""
        close_connection()

    def test_full_workflow(self):
        """完整的工作流测试"""
        # 1. 获取连接
        conn = get_connection()
        assert isinstance(conn, sqlite3.Connection)

        # 2. 使用游标执行操作
        with get_cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS test_integration (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            # 清空可能存在的数据
            cur.execute("DELETE FROM test_integration")
            cur.execute("INSERT INTO test_integration (name) VALUES (?)", ("Alice",))

        # 3. 验证结果
        with get_cursor() as cur:
            cur.execute("SELECT * FROM test_integration")
            result = cur.fetchone()
            assert result["name"] == "Alice"

        # 4. 关闭连接
        close_connection()

        # 5. 验证连接已关闭
        with pytest.raises(sqlite3.ProgrammingError):
            conn.execute("SELECT 1")
