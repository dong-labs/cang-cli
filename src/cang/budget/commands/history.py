"""Budget 预算历史命令

命令:
- history: 显示预算设置历史（按创建时间排序）
"""

import typer
from cang.output.formatter import json_output, InvalidInputError
from cang.budget.repository import list_budgets, PERIOD_TYPES
from cang.db.utils import from_cents

app = typer.Typer(help="预算历史")


@app.command(name="history")
@json_output
def budget_history(
    category: str | None = typer.Option(None, "--category", "-c", help="筛选分类"),
):
    """显示预算设置历史

    按创建时间倒序排列，显示预算的创建和更新历史。
    """
    budgets = list_budgets()

    # 应用筛选
    if category:
        budgets = [b for b in budgets if b["category"] == category]

    # 格式化金额
    result = []
    for b in budgets:
        result.append({
            "id": b["id"],
            "category": b["category"],
            "period": b["period"],
            "amount": from_cents(b["amount_cents"]),
            "created_at": b["created_at"]
        })

    # 按创建时间倒序
    result.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "history": result,
        "count": len(result)
    }
