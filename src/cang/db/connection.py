"""SQLite 数据库连接管理模块

职责:
- 单例模式管理 SQLite 连接
- 确保数据库目录存在
- 提供线程安全的连接管理
- 支持上下文管理器
"""

import sqlite3
import threading
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Iterator

# 全局连接实例（单例）
_connection: sqlite3.Connection | None = None
# 线程安全锁
_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_db_path() -> Path:
    """获取数据库文件路径，确保目录存在

    Returns:
        Path: 数据库文件的绝对路径 (~/.cang/cang.db)
    """
    db_path = Path.home() / ".cang" / "cang.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（单例模式，线程安全）

    使用全局单例模式确保整个应用只有一个连接实例。
    使用 threading.Lock 保证线程安全。

    Returns:
        sqlite3.Connection: SQLite 连接对象，row_factory 设置为 dict 风格
    """
    global _connection

    with _lock:
        if _connection is None:
            db_path = get_db_path()
            # check_same_thread=False 允许在不同线程使用连接
            # 由于我们使用锁保护，这是安全的
            _connection = sqlite3.connect(str(db_path), check_same_thread=False)
            # 设置行工厂为 sqlite3.Row，支持字典风格访问
            _connection.row_factory = sqlite3.Row
        return _connection


def close_connection() -> None:
    """关闭数据库连接

    线程安全地关闭连接并重置单例。
    """
    global _connection

    with _lock:
        if _connection is not None:
            _connection.close()
            _connection = None


@contextmanager
def get_cursor() -> Iterator[sqlite3.Cursor]:
    """获取数据库游标的上下文管理器

    自动管理事务：成功时提交，异常时回滚。
    游标会在上下文退出时自动关闭。

    Yields:
        sqlite3.Cursor: 数据库游标对象

    Example:
        with get_cursor() as cur:
            cur.execute("SELECT * FROM accounts")
            for row in cur.fetchall():
                print(dict(row))
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
