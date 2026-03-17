"""Invest profit 命令

查看投资收益
"""

import typer
from cang.output.formatter import json_output
from cang.db.utils import from_cents

app = typer.Typer(
    name="profit",
    help="查看收益",
    no_args_is_help=True,
)


@app.command()
@json_output
def show(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码"),
    period: str | None = typer.Option("all", "--period", "-p", help="时间周期 (all/ytd/month/week)"),
):
    """查看投资收益"""
    from cang.invest.repository import get_profit

    profit = get_profit(symbol=symbol, period=period)

    return {
        "period": period,
        "symbol_filter": symbol,
        "cost_basis": from_cents(profit["cost_basis_cents"]),
        "proceeds": from_cents(profit["proceeds_cents"]),
        "realized_profit": from_cents(profit["realized_profit_cents"]),
        "dividend": from_cents(profit["dividend_cents"]),
        "total_profit": from_cents(profit["total_profit_cents"]),
    }


@app.command("dividend")
@json_output
def dividend_summary(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码"),
    start: str | None = typer.Option(None, "--start", help="开始日期 (YYYY-MM-DD)"),
    end: str | None = typer.Option(None, "--end", help="结束日期 (YYYY-MM-DD)"),
):
    """分红汇总"""
    from cang.invest.repository import get_dividend_summary

    summary = get_dividend_summary(symbol=symbol, start_date=start, end_date=end)

    result = []
    total = 0
    for item in summary:
        amount = item["total_dividend"]
        total += amount
        result.append({
            "symbol": item["symbol"],
            "total": from_cents(amount),
            "count": item["count"],
        })

    return {
        "total_dividend": from_cents(total),
        "symbols_count": len(result),
        "dividends": result
    }
