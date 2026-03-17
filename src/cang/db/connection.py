"""SQLite 数据库连接管理模块

继承 dong.db.Database，提供 cang-cli 专用数据库访问。
"""

import sqlite3
from typing import Iterator
from contextlib import contextmanager

from dong.db import Database as DongDatabase


class CangDatabase(DongDatabase):
    """仓咚咚数据库类 - 继承自 dong.db.Database

    数据库路径: ~/.dong/cang.db
    """

    @classmethod
    def get_name(cls) -> str:
        return "cang"


# ============================================================================
# 兼容性函数：保持向后兼容
# ============================================================================

def get_db_path():
    """获取数据库文件路径（兼容函数）

    Returns:
        Path: 数据库文件路径
    """
    return CangDatabase.get_db_path()


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（兼容函数）

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    return CangDatabase.get_connection()


def close_connection() -> None:
    """关闭数据库连接（兼容函数）"""
    CangDatabase.close_connection()


@contextmanager
def get_cursor() -> Iterator[sqlite3.Cursor]:
    """获取数据库游标的上下文管理器（兼容函数）

    Yields:
        sqlite3.Cursor: 游标对象
    """
    with CangDatabase.get_cursor() as cur:
        yield cur
