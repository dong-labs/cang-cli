"""Budget 预算状态命令

命令:
- status: 显示预算执行状态（对比实际支出）
"""

import typer
from cang.output.formatter import json_output, InvalidInputError
from cang.budget.repository import (
    get_all_budgets_status,
    PERIOD_TYPES,
)
from cang.db.utils import from_cents

app = typer.Typer(help="预算状态")


@app.command(name="status")
@json_output
def budget_status(
    period: str | None = typer.Option(None, "--period", "-p", help=f"筛选周期: {', '.join(PERIOD_TYPES)}"),
    category: str | None = typer.Option(None, "--category", "-c", help="筛选分类"),
):
    """显示预算执行状态

    对比预算金额和实际支出，计算剩余金额和百分比。
    不指定参数时，显示所有预算的状态。
    """
    # 验证 period 参数
    if period and period not in PERIOD_TYPES:
        raise InvalidInputError(
            f"Invalid period: {period}. Must be one of: {', '.join(PERIOD_TYPES)}"
        )

    statuses = get_all_budgets_status()

    # 应用筛选
    if period:
        statuses = [s for s in statuses if s["period"] == period]
    if category:
        statuses = [s for s in statuses if s["category"] == category]

    # 格式化金额
    result = []
    for s in statuses:
        result.append({
            "id": s["id"],
            "category": s["category"],
            "period": s["period"],
            "start_date": s["start_date"],
            "end_date": s["end_date"],
            "budget": from_cents(s["budget"]),
            "spent": from_cents(s["spent"]),
            "remaining": from_cents(s["remaining"]),
            "percentage": s["percentage"]
        })

    return {
        "statuses": result,
        "count": len(result)
    }
