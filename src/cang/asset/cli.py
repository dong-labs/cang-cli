"""Asset 模块 CLI 定义

职责:
- 定义 asset 子命令的路由
- 注册所有子命令
"""

import typer
from cang.output.formatter import json_output

app = typer.Typer(
    name="asset",
    help="资产存量 - 我拥有什么？",
    no_args_is_help=True,
)

# 注册子命令组
from cang.asset.commands import (
    init,
    list_cmd as asset_list,
    add,
    get,
    update,
    delete,
    networth,
    schema,
)

app.add_typer(init.app, name="init")
app.command("ls")(asset_list.ls_assets)
app.command("add")(add.add_asset)
app.command("get")(get.get_asset)
app.command("update")(update.update_asset_cmd)
app.command("delete")(delete.delete_asset)
app.command("networth")(networth.networth_cmd)
app.command("schema")(schema.asset_schema)
