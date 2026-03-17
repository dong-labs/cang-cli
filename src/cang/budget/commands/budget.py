"""Budget 预算管理命令

命令:
- ls: 列出所有预算
- set: 设置新预算
- get: 获取预算详情
- update: 更新预算金额
- delete: 删除预算
"""

import typer
from cang.output.formatter import json_output, AlreadyExistsError, NotFoundError, InvalidInputError
from cang.budget.repository import (
    list_budgets,
    get_budget_by_id,
    get_budget_by_dates,
    create_budget,
    update_budget,
    delete_budget,
    PERIOD_TYPES,
)
from cang.db.utils import to_cents, from_cents

app = typer.Typer(help="预算管理")


@app.command(name="ls")
@json_output
def list_budgets_cmd(
    period: str | None = typer.Option(None, "--period", "-p", help=f"筛选周期: {', '.join(PERIOD_TYPES)}"),
    category: str | None = typer.Option(None, "--category", "-c", help="筛选分类"),
):
    """列出所有预算

    可以按周期或分类筛选。
    """
    # 验证 period 参数
    if period and period not in PERIOD_TYPES:
        raise InvalidInputError(
            f"Invalid period: {period}. Must be one of: {', '.join(PERIOD_TYPES)}"
        )

    budgets = list_budgets(period=period, category=category)
    return {
        "budgets": budgets,
        "count": len(budgets)
    }


@app.command(name="set")
@json_output
def set_budget(
    category: str = typer.Option(..., "--category", "-c", help="分类名称"),
    amount: float = typer.Option(..., "--amount", "-a", help="预算金额"),
    period: str = typer.Option(..., "--period", "-p", help=f"周期: {', '.join(PERIOD_TYPES)}"),
    start_date: str | None = typer.Option(None, "--start", "-s", help="开始日期 YYYY-MM-DD（可选）"),
    end_date: str | None = typer.Option(None, "--end", "-e", help="结束日期 YYYY-MM-DD（可选）"),
):
    """设置新预算

    如果不指定起止日期，系统将根据 period 自动计算。
    """
    # 验证 period 参数
    if period not in PERIOD_TYPES:
        raise InvalidInputError(
            f"Invalid period: {period}. Must be one of: {', '.join(PERIOD_TYPES)}"
        )

    # 如果提供了日期，检查是否已存在相同配置的预算
    if start_date and end_date:
        existing = get_budget_by_dates(category, start_date, end_date)
        if existing:
            raise AlreadyExistsError(
                f"Budget for category '{category}' with dates {start_date} to {end_date} already exists. Use update to modify."
            )

    amount_cents = to_cents(amount)
    budget = create_budget(category, amount_cents, period, start_date, end_date)

    return {
        "budget": budget,
        "amount": from_cents(budget["amount_cents"])
    }


@app.command(name="get")
@json_output
def get_budget(
    budget_id: int = typer.Option(..., "--id", help="预算 ID"),
):
    """获取预算详情"""
    budget = get_budget_by_id(budget_id)
    if not budget:
        raise NotFoundError(f"Budget with id {budget_id} not found")

    return {
        "budget": budget,
        "amount": from_cents(budget["amount_cents"])
    }


@app.command(name="update")
@json_output
def update_budget_cmd(
    budget_id: int = typer.Option(..., "--id", help="预算 ID"),
    amount: float = typer.Option(..., "--amount", "-a", help="新预算金额"),
):
    """更新预算金额

    只更新金额，不改变其他配置。
    """
    # 检查预算是否存在
    existing = get_budget_by_id(budget_id)
    if not existing:
        raise NotFoundError(f"Budget with id {budget_id} not found")

    amount_cents = to_cents(amount)
    budget = update_budget(budget_id, amount_cents)

    return {
        "budget": budget,
        "amount": from_cents(budget["amount_cents"])
    }


@app.command(name="delete")
@json_output
def delete_budget_cmd(
    budget_id: int = typer.Option(..., "--id", help="预算 ID"),
):
    """删除预算"""
    # 检查预算是否存在
    existing = get_budget_by_id(budget_id)
    if not existing:
        raise NotFoundError(f"Budget with id {budget_id} not found")

    success = delete_budget(budget_id)

    return {
        "deleted": success,
        "budget_id": budget_id,
        "category": existing["category"],
        "period": existing["period"]
    }
