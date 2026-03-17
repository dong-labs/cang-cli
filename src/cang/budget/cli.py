"""Budget 模块 CLI 定义

职责:
- 定义 budget 子命令的路由
- 注册所有子命令
"""

import typer
from cang.output.formatter import json_output

app = typer.Typer(
    name="budget",
    help="预算管理 - 计划花多少？",
    no_args_is_help=True,
)

# 注册子命令组
from cang.budget.commands import budget, status, history, schema, init

app.add_typer(init.app, name="init")
app.add_typer(budget.app, name="budget")
app.add_typer(status.app, name="status")
app.add_typer(history.app, name="history")
app.add_typer(schema.app, name="schema")
