"""Asset init 命令 - 初始化 Asset 模块"""

import typer
from cang.output.formatter import json_output
from cang.db.schema import is_initialized, init_database, SCHEMA_VERSION

app = typer.Typer(help="初始化 asset 模块")


@app.command()
@json_output
def init_asset(force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化")):
    """初始化 asset 模块数据库

    确保 assets 表已创建。使用 --force 可强制重新初始化。
    """
    already_initialized = is_initialized()

    if already_initialized and not force:
        return {
            "message": "Database already initialized",
            "schema_version": SCHEMA_VERSION,
            "module": "asset"
        }

    if force and already_initialized:
        # 强制重新初始化
        pass

    # 初始化数据库
    init_database()

    return {
        "message": "Asset module initialized successfully",
        "schema_version": SCHEMA_VERSION,
        "module": "asset"
    }
