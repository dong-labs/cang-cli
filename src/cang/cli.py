"""Cang CLI - 主入口

职责：
- 创建 Typer 应用
- 注册四个模块子命令
- 统一 JSON 输出和错误处理
"""

import json
import sys
from typing import Any, Optional

import typer

from cang import __version__

# ============================================================================
# 全局配置
# ============================================================================

# 控制 JSON 输出（默认 true，预留未来扩展）
_json_output: bool = True


def set_json_output(enabled: bool) -> None:
    """设置 JSON 输出模式

    Args:
        enabled: 是否启用 JSON 输出
    """
    global _json_output
    _json_output = enabled


def get_json_output() -> bool:
    """获取当前 JSON 输出模式"""
    return _json_output


# ============================================================================
# 版本回调（需要在 app.callback 之前定义）
# ============================================================================

def version_callback(value: bool) -> None:
    """版本号回调函数

    Args:
        value: 是否显示版本
    """
    if value:
        output({
            "name": "cang-cli",
            "version": __version__,
            "description": "仓咚咚 - 个人金融命令行工具 (AI Native)"
        })
        raise typer.Exit()


# ============================================================================
# 主应用
# ============================================================================

app = typer.Typer(
    name="cang",
    help="仓咚咚 (Cang) - 个人金融命令行工具 (AI Native)",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="显示版本信息",
        callback=version_callback,
        is_eager=True,
    ),
    json_output: bool = typer.Option(
        True,
        "--json",
        help="启用 JSON 输出（默认启用）",
    ),
) -> None:
    """主回调函数，处理根级选项

    Args:
        version: 版本号标志
        json_output: JSON 输出标志
    """
    set_json_output(json_output)


# ============================================================================
# 统一输出格式
# ============================================================================

def output(data: Any, success: bool = True) -> None:
    """输出 JSON 格式

    Args:
        data: 要输出的数据
        success: 操作是否成功
    """
    result: dict[str, Any] = {"success": success}
    if success:
        result["data"] = data
    else:
        result["error"] = data
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


def handle_error(e: Exception) -> None:
    """处理异常并输出结构化错误

    Args:
        e: 捕获的异常
    """
    error_info: dict[str, str] = {
        "code": type(e).__name__,
        "message": str(e)
    }
    output(error_info, success=False)
    raise typer.Exit(code=1)


# ============================================================================
# 根级命令
# ============================================================================

@app.command()
def init():
    """初始化 Cang 数据库"""
    from cang.db import init_database

    try:
        init_database()
        output({
            "message": "Cang database initialized successfully",
            "version": __version__
        })
    except Exception as e:
        handle_error(e)


@app.command()
def export(
    output: str = typer.Option("cang.json", "-o", "--output", help="输出文件"),
    format: str = typer.Option("json", "-f", "--format", help="格式: json/md"),
):
    """导出财务数据"""
    from cang.output.export import export as do_export
    
    try:
        do_export(output, format)
    except Exception as e:
        handle_error(e)


@app.command(name="import")
def import_data(
    file: str = typer.Option(..., "-f", "--file", help="导入文件"),
    merge: bool = typer.Option(False, "--merge", help="合并模式"),
    dry_run: bool = typer.Option(False, "--dry-run", help="预览模式"),
):
    """导入财务数据"""
    from cang.output.data_import import import_data as do_import
    
    try:
        do_import(file, merge, dry_run)
    except Exception as e:
        handle_error(e)


# ============================================================================
# 注册模块子命令
# ============================================================================

from cang.fin.cli import app as fin_app
from cang.asset.cli import app as asset_app
from cang.budget.cli import app as budget_app
from cang.invest.cli import app as invest_app

app.add_typer(fin_app, name="fin")
app.add_typer(asset_app, name="asset")
app.add_typer(budget_app, name="budget")
app.add_typer(invest_app, name="invest")


# ============================================================================
# 主入口
# ============================================================================

if __name__ == "__main__":
    app()
