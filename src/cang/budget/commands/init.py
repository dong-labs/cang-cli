"""Budget 初始化命令

命令:
- init: 初始化 budget 模块
"""

import typer
from cang.output.formatter import json_output
from cang.db.schema import init_database, is_initialized, SCHEMA_VERSION


app = typer.Typer(help="Budget 模块初始化")


@app.command(name="init")
@json_output
def budget_init():
    """初始化 budget 模块数据库

    创建 budgets 表。如果数据库已初始化，则确认表存在。
    """
    # 检查是否已初始化
    already_initialized = is_initialized()

    if already_initialized:
        # 数据库已存在，确认表结构
        from cang.db.connection import get_cursor
        with get_cursor() as cur:
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'"
            )
            exists = cur.fetchone() is not None

        return {
            "message": "Database already initialized",
            "schema_version": SCHEMA_VERSION,
            "budgets_table_exists": exists
        }

    # 初始化数据库
    init_database()

    return {
        "message": "Budget module initialized successfully",
        "schema_version": SCHEMA_VERSION
    }
