"""Asset schema 命令 - 显示数据表结构"""

import typer
from cang.output.formatter import json_output
from cang.asset.repository import get_asset_schema


@json_output
def asset_schema():
    """显示 asset 模块的数据库表结构"""
    schema_info = get_asset_schema()

    return {
        "schema": {
            "assets": {
                "columns": schema_info["columns"],
                "asset_types": schema_info["asset_types"]
            }
        }
    }
