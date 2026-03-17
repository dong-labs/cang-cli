"""Invest 模块 CLI 定义

职责:
- 定义 invest 子命令的路由
- 注册所有子命令
"""

import typer
from datetime import datetime
from cang.output.formatter import json_output, InvalidInputError, NotFoundError
from cang.db.utils import to_cents, from_cents

app = typer.Typer(
    name="invest",
    help="投资记录 - 买卖了什么？",
    no_args_is_help=True,
)


def _parse_date(date_str: str | None) -> str:
    """解析日期字符串，如果为空则使用今天"""
    if date_str:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            raise InvalidInputError(f"Invalid date format: {date_str}, expected YYYY-MM-DD")
    return datetime.now().strftime("%Y-%m-%d")


@app.command("init")
@json_output
def init_cmd(force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化")):
    """初始化 invest 模块数据库"""
    from cang.db.schema import is_initialized, SCHEMA_VERSION
    from cang.invest.repository import list_invest_transactions

    if not is_initialized():
        return {
            "success": False,
            "message": "Database not initialized. Run 'cang fin init' first."
        }

    transactions = list_invest_transactions()

    return {
        "message": "Invest module ready",
        "schema_version": SCHEMA_VERSION,
        "existing_transactions": len(transactions)
    }


@app.command("ls")
@json_output
def list_transactions(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码"),
    tx_type: str | None = typer.Option(None, "--type", "-t", help="交易类型 (buy/sell/dividend)"),
    start: str | None = typer.Option(None, "--start", help="开始日期 (YYYY-MM-DD)"),
    end: str | None = typer.Option(None, "--end", help="结束日期 (YYYY-MM-DD)"),
):
    """列出投资交易记录"""
    from cang.invest.repository import list_invest_transactions as ls

    transactions = ls(
        symbol=symbol,
        tx_type=tx_type,
        start_date=start,
        end_date=end,
    )

    return {
        "count": len(transactions),
        "transactions": transactions
    }


@app.command("buy")
@json_output
def buy(
    symbol: str = typer.Option(..., "--symbol", "-s", help="股票代码"),
    price: float = typer.Option(..., "--price", "-p", help="成交价（元）"),
    quantity: float = typer.Option(..., "--quantity", "-q", help="成交数量"),
    date: str | None = typer.Option(None, "--date", "-d", help="交易日期 (YYYY-MM-DD)"),
    fee: float = typer.Option(0, "--fee", "-f", help="手续费（元）"),
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
    )

    return {
        "message": "Dividend recorded",
        "transaction": transaction
    }


@app.command("holdings")
@json_output
def holdings(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码")
):
    """查看当前持仓"""
    from cang.invest.repository import get_holdings

    holdings_list = get_holdings(symbol=symbol)

    result = []
    for h in holdings_list:
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


@app.command("profit")
@json_output
def profit(
    symbol: str | None = typer.Option(None, "--symbol", "-s", help="筛选股票代码"),
    period: str | None = typer.Option("all", "--period", "-p", help="时间周期 (today/week/month/quarter/year/all)"),
):
    """查看投资收益"""
    from cang.invest.repository import get_profit

    profit_data = get_profit(symbol=symbol, period=period)

    return {
        "period": period,
        "symbol_filter": symbol,
        "cost_basis": from_cents(profit_data["cost_basis_cents"]),
        "proceeds": from_cents(profit_data["proceeds_cents"]),
        "realized_profit": from_cents(profit_data["realized_profit_cents"]),
        "dividend": from_cents(profit_data["dividend_cents"]),
        "total_profit": from_cents(profit_data["total_profit_cents"]),
    }


@app.command("schema")
@json_output
def schema(command: str | None = typer.Argument(None, help="命令名称")):
    """查看 invest 模块命令结构"""
    if command:
        # 返回单个命令的帮助信息
        commands_info = {
            "init": {"description": "初始化 invest 模块数据库", "options": ["--force", "-f"]},
            "ls": {"description": "列出投资交易记录", "options": ["--symbol", "--type", "--start", "--end"]},
            "buy": {
                "description": "记录买入",
                "options": [
                    "--symbol TEXT (required)",
                    "--price FLOAT (required)",
                    "--quantity FLOAT (required)",
                    "--date TEXT (optional)",
                    "--fee FLOAT (optional, default 0)"
                ]
            },
            "sell": {
                "description": "记录卖出",
                "options": [
                    "--symbol TEXT (required)",
                    "--price FLOAT (required)",
                    "--quantity FLOAT (required)",
                    "--date TEXT (optional)",
                    "--fee FLOAT (optional, default 0)"
                ]
            },
            "dividend": {
                "description": "记录分红",
                "options": [
                    "--symbol TEXT (required)",
                    "--amount FLOAT (required)",
                    "--date TEXT (optional)"
                ]
            },
            "holdings": {"description": "查看当前持仓", "options": ["--symbol"]},
            "profit": {"description": "查看投资收益", "options": ["--symbol", "--period"]},
            "schema": {"description": "查看命令结构", "options": ["[command]"]},
        }
        return commands_info.get(command, {"error": f"Unknown command: {command}"})

    return {
        "module": "invest",
        "description": "投资记录 - 买卖了什么？",
        "commands": [
            {"name": "init", "description": "初始化 invest 模块数据库"},
            {"name": "ls", "description": "列出投资交易记录"},
            {"name": "buy", "description": "记录买入"},
            {"name": "sell", "description": "记录卖出"},
            {"name": "dividend", "description": "记录分红"},
            {"name": "holdings", "description": "查看当前持仓"},
            {"name": "profit", "description": "查看投资收益"},
            {"name": "schema", "description": "查看命令结构"},
        ],
        "database": {
            "table": "invest_transactions",
            "columns": [
                "id INTEGER PRIMARY KEY",
                "type TEXT (buy/sell/dividend)",
                "symbol TEXT",
                "price_cents INTEGER",
                "quantity REAL",
                "amount_cents INTEGER",
                "fee_cents INTEGER",
                "date TEXT",
                "created_at TEXT"
            ]
        }
    }
