"""Invest 交易命令

包含 ls, buy, sell, dividend 子命令
"""

import typer
from datetime import datetime
from cang.output.formatter import json_output, InvalidInputError
from cang.db.utils import to_cents

app = typer.Typer(
    name="tx",
    help="投资交易操作",
    no_args_is_help=True,
)


def _parse_date(date_str: str | None) -> str:
    """解析日期字符串，如果为空则使用今天

    Args:
        date_str: 日期字符串 (YYYY-MM-DD)

    Returns:
        格式化的日期字符串
    """
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            raise InvalidInputError(f"Invalid date format: {date_str}, expected YYYY-MM-DD")
    return datetime.now().strftime("%Y-%m-%d")


@app.command("ls")
@json_output
def list_transactions(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码"),
    tx_type: str | None = typer.Option(None, "--type", "-t", help="交易类型 (buy/sell/dividend)"),
    start: str | None = typer.Option(None, "--start", help="开始日期 (YYYY-MM-DD)"),
    end: str | None = typer.Option(None, "--end", help="结束日期 (YYYY-MM-DD)"),
    limit: int | None = typer.Option(None, "--limit", "-n", help="限制返回数量"),
):
    """列出投资交易记录"""
    from cang.invest.repository import list_invest_transactions as ls

    transactions = ls(
        symbol=symbol,
        tx_type=tx_type,
        start_date=start,
        end_date=end,
        limit=limit,
    )

    return {
        "count": len(transactions),
        "transactions": transactions
    }


@app.command("get")
@json_output
def get_transaction(
    tx_id: int = typer.Argument(..., help="交易 ID")
):
    """获取单个交易详情"""
    from cang.invest.repository import get_invest_transaction_by_id
    from cang.output.formatter import NotFoundError

    transaction = get_invest_transaction_by_id(tx_id)
    if not transaction:
        raise NotFoundError(f"Transaction {tx_id} not found")

    return transaction


@app.command("buy")
@json_output
def buy(
    symbol: str = typer.Option(..., "--symbol", "-s", help="股票代码"),
    price: float = typer.Option(..., "--price", "-p", help="成交价（元）"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="成交数量"),
    date: str | None = typer.Option(None, "--date", "-d", help="交易日期 (YYYY-MM-DD)"),
    fee: float = typer.Option(0, "--fee", "-f", help="手续费（元）"),
    note: str | None = typer.Option(None, "--note", help="备注"),
):
    """记录买入"""
    from cang.invest.repository import create_invest_transaction

    date_str = _parse_date(date)
    price_cents = to_cents(price)
    fee_cents = to_cents(fee)
    amount_cents = int(price_cents * quantity)

    transaction = create_invest_transaction(
        date=date_str,
        symbol=symbol,
        tx_type="buy",
        price_cents=price_cents,
        quantity=quantity,
        amount_cents=amount_cents,
        fee_cents=fee_cents,
        note=note,
    )

    return {
        "message": "Buy transaction recorded",
        "transaction": transaction
    }


@app.command("sell")
@json_output
def sell(
    symbol: str = typer.Option(..., "--symbol", "-s", help="股票代码"),
    price: float = typer.Option(..., "--price", "-p", help="成交价（元）"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="成交数量"),
    date: str | None = typer.Option(None, "--date", "-d", help="交易日期 (YYYY-MM-DD)"),
    fee: float = typer.Option(0, "--fee", "-f", help="手续费（元）"),
    note: str | None = typer.Option(None, "--note", help="备注"),
):
    """记录卖出"""
    from cang.invest.repository import create_invest_transaction

    date_str = _parse_date(date)
    price_cents = to_cents(price)
    fee_cents = to_cents(fee)
    amount_cents = int(price_cents * quantity)

    transaction = create_invest_transaction(
        date=date_str,
        symbol=symbol,
        tx_type="sell",
        price_cents=price_cents,
        quantity=quantity,
        amount_cents=amount_cents,
        fee_cents=fee_cents,
        note=note,
    )

    return {
        "message": "Sell transaction recorded",
        "transaction": transaction
    }


@app.command("dividend")
@json_output
def dividend(
    symbol: str = typer.Option(..., "--symbol", "-s", help="股票代码"),
    amount: float = typer.Option(..., "--amount", "-a", help="分红金额（元）"),
    date: str | None = typer.Option(None, "--date", "-d", help="分红日期 (YYYY-MM-DD)"),
    note: str | None = typer.Option(None, "--note", help="备注"),
):
    """记录分红"""
    from cang.invest.repository import create_invest_transaction

    date_str = _parse_date(date)
    amount_cents = to_cents(amount)

    transaction = create_invest_transaction(
        date=date_str,
        symbol=symbol,
        tx_type="dividend",
        price_cents=0,
        quantity=0,
        amount_cents=amount_cents,
        fee_cents=0,
        note=note,
    )

    return {
        "message": "Dividend recorded",
        "transaction": transaction
    }
