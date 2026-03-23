"""Transaction 命令组 - 交易管理

命令:
- ls: 列出交易记录
- add: 添加新交易
- get: 获取交易详情
- update: 更新交易
- delete: 删除交易
- summary: 交易汇总
"""

import typer
from datetime import date, datetime, timedelta
from cang.output.formatter import json_output, NotFoundError, InvalidInputError
from cang.fin.repository import (
    list_transactions,
    get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_transaction_summary,
    get_account_by_id,
)
from cang.db.utils import to_cents, from_cents

app = typer.Typer(help="交易管理")


def _parse_period(period: str) -> tuple[str, str]:
    """将 period 转换为开始和结束日期

    Args:
        period: today | week | month | quarter | year

    Returns:
        (start_date, end_date) 格式的元组
    """
    today = date.today()

    if period == "today":
        start = end = today.isoformat()
    elif period == "week":
        # 本周一到今天
        start = (today - timedelta(days=today.weekday())).isoformat()
        end = today.isoformat()
    elif period == "month":
        # 本月1日到今天
        start = today.replace(day=1).isoformat()
        end = today.isoformat()
    elif period == "quarter":
        # 本季度第一天到今天
        quarter = (today.month - 1) // 3 + 1
        start = today.replace(month=(quarter - 1) * 3 + 1, day=1).isoformat()
        end = today.isoformat()
    elif period == "year":
        # 今年1月1日到今天
        start = today.replace(month=1, day=1).isoformat()
        end = today.isoformat()
    else:
        raise InvalidInputError(f"Invalid period: {period}. Must be one of: today, week, month, quarter, year")

    return start, end


@app.command(name="list")
@json_output
def list_tx(
    limit: int | None = typer.Option(None, "--limit", "-l", help="限制数量"),
    offset: int | None = typer.Option(0, "--offset", "-o", help="跳过数量"),
    account: int | None = typer.Option(None, "--account", "-a", help="账户 ID"),
    start: str | None = typer.Option(None, "--start", "-s", help="开始日期 (YYYY-MM-DD)"),
    end: str | None = typer.Option(None, "--end", "-e", help="结束日期 (YYYY-MM-DD)"),
    category: str | None = typer.Option(None, "--category", "-c", help="分类"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="按标签筛选"),
):
    """列出交易记录

    支持按账户、日期范围、分类、标签筛选，可限制和偏移数量。
    """
    # 获取所有交易（repository 需要支持更多筛选条件）
    # 这里先获取基础列表，然后在内存中筛选
    transactions = list_transactions(
        limit=None,  # 获取全部，然后在内存中处理 offset/limit
        account_id=account,
        category=category
    )

    # 按标签筛选
    if tag:
        transactions = [t for t in transactions if tag in (t.get("tags") or "")]

    # 按日期筛选
    if start:
        transactions = [t for t in transactions if t["date"] >= start]
    if end:
        transactions = [t for t in transactions if t["date"] <= end]

    # 获取总数（在 offset 之前）
    total = len(transactions)

    # 应用 offset 和 limit
    if offset:
        transactions = transactions[offset:]
    if limit:
        transactions = transactions[:limit]

    return {
        "transactions": transactions,
        "count": len(transactions),
        "total": total
    }


@app.command(name="add")
@json_output
def add_tx(
    amount: float = typer.Option(..., "--amount", help="金额（正数为收入，负数为支出）"),
    account: int = typer.Option(..., "--account", "-a", help="账户 ID"),
    category: str | None = typer.Option(None, "--category", "-c", help="分类"),
    note: str | None = typer.Option(None, "--note", "-n", help="备注"),
    tags: str | None = typer.Option(None, "--tags", help="标签（逗号分隔）"),
    tx_date: str | None = typer.Option(None, "--date", "-d", help="日期 (YYYY-MM-DD)，默认今天"),
):
    """添加新交易

    金额为正数表示收入，负数表示支出。
    默认使用今天日期。
    """
    # 验证账户存在
    acc = get_account_by_id(account)
    if not acc:
        raise NotFoundError(f"Account with id {account} not found")

    # 默认日期为今天
    if tx_date is None:
        tx_date = date.today().isoformat()

    # 转换金额为分
    amount_cents = to_cents(amount)

    transaction = create_transaction(
        date=tx_date,
        amount_cents=amount_cents,
        account_id=account,
        category=category,
        note=note,
        tags=tags
    )

    return {
        "transaction": transaction,
        "message": "Transaction added"
    }


@app.command(name="get")
@json_output
def get_tx(
    tx_id: int = typer.Option(..., "--id", help="交易 ID")
):
    """获取交易详情"""
    transaction = get_transaction_by_id(tx_id)
    if not transaction:
        raise NotFoundError(f"Transaction with id {tx_id} not found")

    return {"transaction": transaction}


@app.command(name="update")
@json_output
def update_tx(
    tx_id: int = typer.Option(..., "--id", help="交易 ID"),
    amount: float | None = typer.Option(None, "--amount", help="新金额"),
    account: int | None = typer.Option(None, "--account", "-a", help="新账户 ID"),
    category: str | None = typer.Option(None, "--category", "-c", help="新分类"),
    note: str | None = typer.Option(None, "--note", "-n", help="新备注"),
    tags: str | None = typer.Option(None, "--tags", help="新标签"),
):
    """更新交易

    只更新提供的字段，未提供的字段保持不变。
    """
    # 检查交易是否存在
    existing = get_transaction_by_id(tx_id)
    if not existing:
        raise NotFoundError(f"Transaction with id {tx_id} not found")

    # 如果提供了 account，验证账户存在
    if account is not None:
        acc = get_account_by_id(account)
        if not acc:
            raise NotFoundError(f"Account with id {account} not found")

    # 转换金额
    amount_cents = to_cents(amount) if amount is not None else None

    transaction = update_transaction(
        tx_id=tx_id,
        amount_cents=amount_cents,
        account_id=account,
        category=category,
        note=note,
        tags=tags
    )

    return {
        "transaction": transaction,
        "message": "Transaction updated"
    }


@app.command(name="delete")
@json_output
def delete_tx(
    tx_id: int = typer.Option(..., "--id", help="交易 ID")
):
    """删除交易"""
    # 检查交易是否存在
    existing = get_transaction_by_id(tx_id)
    if not existing:
        raise NotFoundError(f"Transaction with id {tx_id} not found")

    success = delete_transaction(tx_id)
    if not success:
        raise InvalidInputError(f"Failed to delete transaction {tx_id}")

    return {
        "message": f"Transaction {tx_id} deleted",
        "id": tx_id
    }


@app.command(name="summary")
@json_output
def summary(
    period: str | None = typer.Option(None, "--period", "-p", help="时间范围: today|week|month|quarter|year"),
    start: str | None = typer.Option(None, "--start", "-s", help="开始日期 (YYYY-MM-DD)"),
    end: str | None = typer.Option(None, "--end", "-e", help="结束日期 (YYYY-MM-DD)"),
    category: str | None = typer.Option(None, "--category", "-c", help="筛选分类"),
    account: int | None = typer.Option(None, "--account", "-a", help="筛选账户 ID"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="筛选标签"),
):
    """交易汇总统计

    计算指定时间范围内的收入、支出和净额。
    --period 和 --start/--end 互斥，优先使用 --period。
    """
    # 处理日期范围
    if period:
        start_date, end_date = _parse_period(period)
    elif start or end:
        start_date = start or ""
        end_date = end or date.today().isoformat()
    else:
        # 默认为本月
        start_date, end_date = _parse_period("month")

    # 获取交易数据
    transactions = list_transactions(
        limit=None,
        account_id=account,
        category=category
    )

    # 按标签筛选
    if tag:
        transactions = [t for t in transactions if tag in (t.get("tags") or "")]

    # 按日期筛选
    filtered = [
        t for t in transactions
        if t["date"] >= start_date and t["date"] <= end_date
    ]

    # 计算汇总
    income_cents = sum(t["amount_cents"] for t in filtered if t["amount_cents"] > 0)
    expense_cents = sum(abs(t["amount_cents"]) for t in filtered if t["amount_cents"] < 0)
    net_cents = income_cents - expense_cents

    # 按标签统计
    tag_counter = {}
    for t in filtered:
        tags = t.get("tags") or ""
        if tags:
            for tg in tags.split(","):
                tg = tg.strip()
                if tg:
                    tag_counter[tg] = tag_counter.get(tg, 0) + abs(t["amount_cents"])

    return {
        "period": period or "custom",
        "start_date": start_date,
        "end_date": end_date,
        "income": from_cents(income_cents),
        "expense": from_cents(expense_cents),
        "net": from_cents(net_cents),
        "income_cents": income_cents,
        "expense_cents": expense_cents,
        "net_cents": net_cents,
        "transaction_count": len(filtered),
        "by_tag": tag_counter
    }
