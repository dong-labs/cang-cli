"""统一的输出格式化 - 使用 dong-core

此模块保留作为兼容层，内部委托给 dong-core。
"""

import json
from typing import Any

import typer
from dong.output.formatter import json_output as _json_output
from dong.errors.exceptions import (
    DongError,
    ValidationError,
    NotFoundError,
    ConflictError,
)

# 导出旧的类名作为别名，保持向后兼容
CangError = DongError
DatabaseError = DongError
InvalidInputError = ValidationError
AlreadyExistsError = ConflictError


def success(data: Any) -> None:
    """输出成功响应"""
    result = {"success": True, "data": data}
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


def error(code: str, message: str) -> None:
    """输出错误响应"""
    result = {"success": False, "error": {"code": code, "message": message}}
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


def error_from_exception(e: Exception) -> None:
    """从异常输出错误"""
    error(type(e).__name__, str(e))
    raise typer.Exit(code=1)


def print_json(data: Any) -> None:
    """输出 JSON 数据"""
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


__all__ = [
    # 从 dong-core
    "json_output",
    "DongError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    # 向后兼容的别名
    "CangError",
    "DatabaseError",
    "InvalidInputError",
    "AlreadyExistsError",
    # 兼容函数
    "success",
    "error",
    "error_from_exception",
    "print_json",
]
