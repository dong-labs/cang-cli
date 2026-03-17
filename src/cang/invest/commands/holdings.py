"""Invest holdings 命令

查看当前持仓
"""

import typer
from cang.output.formatter import json_output
from cang.db.utils import from_cents

app = typer.Typer(
    name="holdings",
    help="查看持仓",
    no_args_is_help=True,
)


@app.command()
@json_output
def show(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码")
):
    """查看当前持仓"""
    from cang.invest.repository import get_holdings

    holdings = get_holdings(symbol=symbol)

    # 格式化金额显示
    result = []
    for h in holdings:
        result.append({
            "symbol": h["symbol"],
            "quantity": h["quantity"],
            "avg_cost": from_cents(h["avg_cost_cents"]),
            "last_price": from_cents(h["last_price_cents"]),
            "cost": from_cents(h["cost_cents"]),
            "market_value": from_cents(h["market_value_cents"]),
            "profit": from_cents(h["profit_cents"]),
        })

    return {
        "count": len(result),
        "holdings": result
    }


@app.command("summary")
@json_output
def summary():
    """持仓汇总统计"""
    from cang.invest.repository import get_holdings

    holdings = get_holdings()

    total_cost = sum(h["cost_cents"] for h in holdings)
    total_market_value = sum(h["market_value_cents"] for h in holdings)
    total_profit = sum(h["profit_cents"] for h in holdings)

    return {
        "symbols_count": len(holdings),
        "total_cost": from_cents(total_cost),
        "total_market_value": from_cents(total_market_value),
        "total_profit": from_cents(total_profit),
        "profit_ratio": f"{total_profit / total_cost * 100:.2f}%" if total_cost > 0 else "0%"
    }
