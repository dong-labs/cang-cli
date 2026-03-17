"""Invest schema 命令

显示 invest 模块的数据库表结构
"""

import typer
from cang.output.formatter import json_output

app = typer.Typer(
    name="schema",
    help="显示 invest 模块数据库表结构",
    no_args_is_help=True,
)


@app.command()
@json_output
def show():
    """显示 invest 模块的数据库表结构"""
    return {
        "schema": {
            "invest_transactions": {
                "description": "投资交易记录表",
                "columns": [
                    "id - 主键",
                    "date - 交易日期 (YYYY-MM-DD)",
                    "symbol - 股票代码",
                    "type - 交易类型 (buy/sell/dividend)",
                    "price_cents - 成交价（分）",
                    "quantity - 成交数量",
                    "amount_cents - 成交金额（分）",
                    "fee_cents - 手续费（分）",
                    "note - 备注",
                    "created_at - 创建时间"
                ]
            }
        }
    }
