"""Category 命令组 - 分类管理

命令:
- ls: 列出所有分类
- add: 添加新分类
"""

import typer
from cang.output.formatter import json_output, AlreadyExistsError, NotFoundError
from cang.fin.repository import (
    list_categories,
    get_category_by_name,
    create_category,
)

app = typer.Typer(help="分类管理")


@app.command(name="ls")
@json_output
def list_categories_cmd():
    """列出所有分类"""
    categories = list_categories()
    return {"categories": categories}


@app.command(name="add")
@json_output
def add_category(
    name: str = typer.Argument(..., help="分类名称")
):
    """添加新分类

    如果分类已存在，返回错误。
    """
    # 检查是否已存在
    existing = get_category_by_name(name)
    if existing:
        raise AlreadyExistsError(f"Category '{name}' already exists")

    category = create_category(name)
    return {
        "category": category,
        "message": f"Category '{name}' added"
    }
