"""Budget Schema 命令

命令:
- schema: 显示 budget 模块的数据库表结构
"""

import typer
from cang.output.formatter import json_output

app = typer.Typer(help="Budget 模块表结构")


@app.command(name="schema")
@json_output
def budget_schema():
    """显示 budget 模块的数据库表结构"""
    return {
        "schema": {
            "budgets": {
                "description": "预算设置表",
                "columns": [
                    {"name": "id", "type": "INTEGER", "description": "主键"},
                    {"name": "category", "type": "TEXT", "description": "分类名称"},
                    {"name": "amount_cents", "type": "INTEGER", "description": "预算金额（分）"},
                    {"name": "period", "type": "TEXT", "description": "周期 (week/month/quarter/year)"},
                    {"name": "start_date", "type": "TEXT", "description": "开始日期 YYYY-MM-DD"},
                    {"name": "end_date", "type": "TEXT", "description": "结束日期 YYYY-MM-DD"},
                    {"name": "created_at", "type": "TEXT", "description": "创建时间"}
                ]
            },
            "period_values": {
                "week": "周预算",
                "month": "月预算",
                "quarter": "季度预算",
                "year": "年预算"
            },
            "related_tables": {
                "transactions": {
                    "description": "交易记录表（用于计算实际支出）",
                    "note": "status 命令会查询此表对比实际支出"
                }
            }
        }
    }
