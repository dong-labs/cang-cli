"""Invest 模块数据访问层

职责:
- 封装所有投资交易相关的数据库操作
- 提供类型化的数据访问接口
- 处理持仓计算和收益计算
"""

from datetime import datetime
from cang.db.connection import get_cursor


# ============================================================================
# 投资交易操作
# ============================================================================

def list_invest_transactions(
    symbol: str | None = None,
    tx_type: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """列出投资交易记录

    Args:
        symbol: 筛选指定股票代码
        tx_type: 筛选交易类型 (buy/sell/dividend)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        limit: 限制返回数量

    Returns:
        交易列表
    """
    query = "SELECT * FROM invest_transactions"
    params = []
    conditions = []

    if symbol:
        conditions.append("symbol = ?")
        params.append(symbol.upper())
    if tx_type:
        conditions.append("type = ?")
        params.append(tx_type)
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date DESC, id DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_invest_transaction_by_id(tx_id: int) -> dict | None:
    """根据 ID 获取投资交易

    Args:
        tx_id: 交易 ID

    Returns:
        交易信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM invest_transactions WHERE id = ?", (tx_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_invest_transaction(
    date: str,
    symbol: str,
    tx_type: str,
    price_cents: int,
    quantity: float,
    amount_cents: int,
    fee_cents: int = 0,
    note: str | None = None,
) -> dict:
    """创建新的投资交易

    Args:
        date: 日期字符串 (YYYY-MM-DD)
        symbol: 股票代码
        tx_type: 交易类型 (buy/sell/dividend)
        price_cents: 成交价（分）
        quantity: 成交数量
        amount_cents: 成交金额（分）
        fee_cents: 手续费（分）
        note: 备注

    Returns:
        新创建的交易信息
    """
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO invest_transactions
               (date, symbol, type, price_cents, quantity, amount_cents, fee_cents, note)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, symbol.upper(), tx_type, price_cents, quantity, amount_cents, fee_cents, note)
        )
        return get_invest_transaction_by_id(cur.lastrowid)


# ============================================================================
# 持仓计算
# ============================================================================

def get_holdings(symbol: str | None = None) -> list[dict]:
    """计算当前持仓

    对于每个 symbol:
    - quantity = SUM(buy.quantity) - SUM(sell.quantity)
    - avg_cost = SUM(buy.amount + buy.fee) / SUM(buy.quantity)
    - current_value 使用最新买入价估算

    Args:
        symbol: 筛选指定股票代码

    Returns:
        持仓列表
    """
    # 获取所有买入和卖出记录
    query = """
        SELECT symbol, type, SUM(quantity) as total_qty, SUM(amount_cents) as total_amount, SUM(fee_cents) as total_fee
        FROM invest_transactions
        WHERE type IN ('buy', 'sell')
    """
    params = []
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol.upper())

    query += " GROUP BY symbol, type"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    # 按 symbol 聚合
    holdings_dict = {}
    for row in rows:
        row = dict(row)
        sym = row["symbol"]
        if sym not in holdings_dict:
            holdings_dict[sym] = {"buy_qty": 0, "sell_qty": 0, "buy_amount": 0, "buy_fee": 0}

        if row["type"] == "buy":
            holdings_dict[sym]["buy_qty"] += row["total_qty"]
            holdings_dict[sym]["buy_amount"] += row["total_amount"]
            holdings_dict[sym]["buy_fee"] += row["total_fee"]
        else:  # sell
            holdings_dict[sym]["sell_qty"] += row["total_qty"]

    # 计算持仓
    result = []
    for symbol, data in holdings_dict.items():
        quantity = data["buy_qty"] - data["sell_qty"]

        if quantity <= 0:
            continue  # 已清仓或卖空（暂不支持）

        # 计算平均成本
        total_cost = data["buy_amount"] + data["buy_fee"]
        avg_cost_cents = int(total_cost / data["buy_qty"]) if data["buy_qty"] > 0 else 0

        # 获取最新成交价（用最后一次 buy 的价格）
        with get_cursor() as cur:
            cur.execute(
                """SELECT price_cents FROM invest_transactions
                   WHERE symbol = ? AND type = 'buy'
                   ORDER BY date DESC, id DESC LIMIT 1""",
                (symbol,)
            )
            price_row = cur.fetchone()
            last_price_cents = price_row["price_cents"] if price_row else avg_cost_cents

        result.append({
            "symbol": symbol,
            "quantity": quantity,
            "avg_cost_cents": avg_cost_cents,
            "last_price_cents": last_price_cents,
            "cost_cents": int(quantity * avg_cost_cents),
            "market_value_cents": int(quantity * last_price_cents),
            "profit_cents": int(quantity * (last_price_cents - avg_cost_cents)),
        })

    return sorted(result, key=lambda x: x["symbol"])


# ============================================================================
# 收益计算
# ============================================================================

def get_profit(
    symbol: str | None = None,
    period: str | None = None,
) -> dict:
    """计算投资收益

    realized_profit: 已实现收益 = 卖出金额 - 卖出成本 - 手续费
    cost_basis: 成本基数 = 买入金额 + 买入费用
    proceeds: 变现金额 = 卖出金额 - 卖出费用

    Args:
        symbol: 筛选指定股票代码
        period: 时间周期 (all/ytd/month/week)，暂只支持 all

    Returns:
        收益统计
    """
    query = """
        SELECT symbol, type,
               SUM(amount_cents) as total_amount,
               SUM(fee_cents) as total_fee,
               SUM(quantity) as total_quantity
        FROM invest_transactions
        WHERE type IN ('buy', 'sell')
    """
    params = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol.upper())

    if period == "today":
        query += " AND date = DATE('now')"
    elif period == "week":
        query += " AND date >= DATE('now', '-7 days')"
    elif period == "month":
        query += " AND date >= DATE('now', 'start of month')"
    elif period == "quarter":
        query += " AND date >= DATE('now', 'start of year', '+' || (CAST(strftime('%m', 'now') AS INTEGER) - 1) / 3 || ' months')"
    elif period == "year" or period == "ytd":
        query += " AND date >= DATE('now', 'start of year')"

    query += " GROUP BY symbol, type"

    with get_cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    # 按类型汇总
    buy_amount = 0
    buy_fee = 0
    sell_amount = 0
    sell_fee = 0

    for row in rows:
        row = dict(row)
        if row["type"] == "buy":
            buy_amount += row["total_amount"]
            buy_fee += row["total_fee"]
        else:  # sell
            sell_amount += row["total_amount"]
            sell_fee += row["total_fee"]

    # 计算收益
    cost_basis = buy_amount + buy_fee
    proceeds = sell_amount - sell_fee
    realized_profit = proceeds - cost_basis

    # 获取分红收入
    div_query = """
        SELECT COALESCE(SUM(amount_cents), 0) as total_div
        FROM invest_transactions
        WHERE type = 'dividend'
    """
    div_params = []
    if symbol:
        div_query += " AND symbol = ?"
        div_params.append(symbol.upper())

    if period == "today":
        div_query += " AND date = DATE('now')"
    elif period == "week":
        div_query += " AND date >= DATE('now', '-7 days')"
    elif period == "month":
        div_query += " AND date >= DATE('now', 'start of month')"
    elif period == "quarter":
        div_query += " AND date >= DATE('now', 'start of year', '+' || (CAST(strftime('%m', 'now') AS INTEGER) - 1) / 3 || ' months')"
    elif period == "year" or period == "ytd":
        div_query += " AND date >= DATE('now', 'start of year')"

    with get_cursor() as cur:
        cur.execute(div_query, div_params)
        div_row = cur.fetchone()
        dividend_income = div_row["total_div"] if div_row else 0

    return {
        "cost_basis_cents": cost_basis,
        "proceeds_cents": proceeds,
        "realized_profit_cents": realized_profit,
        "dividend_cents": dividend_income,
        "total_profit_cents": realized_profit + dividend_income,
    }


def get_dividend_summary(
    symbol: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """获取分红汇总

    Args:
        symbol: 筛选指定股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        分红汇总列表，按 symbol 分组
    """
    query = """
        SELECT symbol, SUM(amount_cents) as total_dividend, COUNT(*) as count
        FROM invest_transactions
        WHERE type = 'dividend'
    """
    params = []

    if symbol:
        query += " AND symbol = ?"
        params.append(symbol.upper())
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " GROUP BY symbol ORDER BY total_dividend DESC"

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
