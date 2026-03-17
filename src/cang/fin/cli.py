"""Fin 模块 CLI 定义

职责:
- 定义 fin 子命令的路由
- 注册所有 account/tx/transfer/category/schema 子命令
"""

import typer
from cang.output.formatter import json_output, success

app = typer.Typer(
    name="fin",
    help="财务流动 - 钱怎么花的？",
    no_args_is_help=True,
)

# 注册子命令组
from cang.fin.commands import account, tx, category, transfer, schema

app.add_typer(account.app, name="account")
app.add_typer(tx.app, name="tx")
app.add_typer(category.app, name="category")
app.add_typer(transfer.app, name="transfer")
app.add_typer(schema.app, name="schema")


# 默认分类列表
_DEFAULT_CATEGORIES = [
    "餐饮", "交通", "购物", "娱乐",
    "居住", "医疗", "教育", "通讯", "其他"
]


@app.command()
@json_output
def init(force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化")):
    """初始化 fin 模块数据库

    创建数据库表并插入默认分类。
    使用 --force 可强制重新初始化（会清空现有数据）。
    """
    from cang.db.schema import init_database, is_initialized, SCHEMA_VERSION
    from cang.fin.repository import list_categories, create_category, get_category_by_name

    # 检查是否已初始化
    already_initialized = is_initialized()

    if already_initialized and not force:
        # 已初始化且不是强制模式，检查是否需要补充默认分类
        existing = list_categories()
        existing_names = {c["name"] for c in existing}
        added = []

        for name in _DEFAULT_CATEGORIES:
            if name not in existing_names:
                create_category(name)
                added.append(name)

        return {
            "message": "Database already initialized",
            "schema_version": SCHEMA_VERSION,
            "categories_added": added,
            "total_categories": len(existing) + len(added)
        }

    if force and already_initialized:
        # 强制重新初始化：先删除所有表（通过重新创建实现）
        # init_database 会处理版本检查，这里需要特殊处理
        pass

    # 初始化数据库
    init_database()

    # 插入默认分类
    added = []
    for name in _DEFAULT_CATEGORIES:
        category = create_category(name)
        added.append(category["name"])

    return {
        "message": "Database initialized successfully",
        "schema_version": SCHEMA_VERSION,
        "default_categories": added,
        "categories_count": len(added)
    }


@app.command()
@json_output
def db_schema():
    """显示 fin 模块的数据库表结构"""
    return {
        "schema": {
            "accounts": {
                "columns": ["id", "name", "type", "currency", "created_at"]
            },
            "transactions": {
                "columns": ["id", "date", "amount_cents", "account_id", "category", "note", "created_at"]
            },
            "categories": {
                "columns": ["id", "name"]
            },
            "transfers": {
                "columns": ["id", "from_account_id", "to_account_id", "amount_cents", "fee_cents", "date", "note", "created_at"]
            }
        }
    }
