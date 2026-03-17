"""Budget 模块数据访问层

职责:
- 封装所有预算相关的数据库操作
- 提供类型化的数据访问接口
- 处理金额转换 (分 <-> 元)
- 查询实际支出（需要关联 transactions 表）
"""

from datetime import datetime
from cang.db.connection import get_cursor


# 支持的预算周期
PERIOD_TYPES = ["week", "month", "quarter", "year"]


def _get_period_dates(period: str) -> tuple[str, str]:
    """根据周期计算起止日期

    Args:
        period: 周期类型 (week/month/quarter/year)

    Returns:
        (start_date, end_date) YYYY-MM-DD 格式的元组
    """
    from datetime import timedelta
    now = datetime.now()
    year = now.year
    month = now.month
    day = now.day

    if period == "week":
        # 本周（周一到周日）
        weekday = now.weekday()  # 0=周一, 6=周日
        start = now - timedelta(days=weekday)
        end = start + timedelta(days=6)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    elif period == "month":
        # 本月第一天到最后一天
        start = now.replace(day=1)
        if month == 12:
            end = now.replace(year=year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = now.replace(month=month + 1, day=1) - timedelta(days=1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    elif period == "quarter":
        # 本季度
        quarter = (month - 1) // 3
        start_month = quarter * 3 + 1
        end_month = start_month + 2

        # 季度初
        start = now.replace(month=start_month, day=1)

        # 季度末（下月第一天减一天）
        if end_month == 12:
            end = now.replace(year=year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = now.replace(month=end_month + 1, day=1) - timedelta(days=1)

        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    elif period == "year":
        # 本年
        start = now.replace(month=1, day=1)
        end = now.replace(month=12, day=31)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    else:
        raise ValueError(f"Invalid period: {period}")


# ============================================================================
# Budget 相关操作
# ============================================================================

def list_budgets(
    period: str | None = None,
    category: str | None = None
) -> list[dict]:
    """列出预算

    Args:
        period: 筛选指定周期
        category: 筛选指定分类

    Returns:
        预算列表
    """
    query = "SELECT * FROM budgets"
    params = []
    conditions = []

    if category:
        conditions.append("category = ?")
        params.append(category)
    if period:
        conditions.append("period = ?")
        params.append(period)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY category, period"

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_budget_by_id(budget_id: int) -> dict | None:
    """根据 ID 获取预算

    Args:
        budget_id: 预算 ID

    Returns:
        预算信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM budgets WHERE id = ?", (budget_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_budget_by_dates(category: str, start_date: str, end_date: str) -> dict | None:
    """根据分类和日期范围获取预算

    Args:
        category: 分类名称
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        预算信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM budgets WHERE category = ? AND start_date = ? AND end_date = ?",
            (category, start_date, end_date)
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_budget(
    category: str,
    amount_cents: int,
    period: str,
    start_date: str | None = None,
    end_date: str | None = None
) -> dict:
    """创建新预算

    Args:
        category: 分类名称
        amount_cents: 预算金额（分）
        period: 周期 (week/month/quarter/year)
        start_date: 开始日期（可选，默认自动计算）
        end_date: 结束日期（可选，默认自动计算）

    Returns:
        新创建的预算信息
    """
    if start_date is None or end_date is None:
        start_date, end_date = _get_period_dates(period)

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO budgets (category, amount_cents, period, start_date, end_date)
               VALUES (?, ?, ?, ?, ?)""",
            (category, amount_cents, period, start_date, end_date)
        )
        return get_budget_by_id(cur.lastrowid)


def update_budget(budget_id: int, amount_cents: int) -> dict | None:
    """更新预算金额

    Args:
        budget_id: 预算 ID
        amount_cents: 新金额（分）

    Returns:
        更新后的预算信息，如果预算不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute(
            "UPDATE budgets SET amount_cents = ? WHERE id = ?",
            (amount_cents, budget_id)
        )
        return get_budget_by_id(budget_id)


def delete_budget(budget_id: int) -> bool:
    """删除预算

    Args:
        budget_id: 预算 ID

    Returns:
        是否成功删除
    """
    with get_cursor() as cur:
        cur.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        return cur.rowcount > 0


# ============================================================================
# 实际支出查询
# ============================================================================

def get_budget_spent(category: str, start_date: str, end_date: str) -> int:
    """获取指定分类和日期范围的实际支出

    Args:
        category: 分类名称
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD

    Returns:
        实际支出金额（分）
    """
    query = """
        SELECT COALESCE(SUM(amount_cents), 0) as total
        FROM transactions
        WHERE category = ? AND date >= ? AND date <= ?
    """

    with get_cursor() as cur:
        cur.execute(query, (category, start_date, end_date))
        return cur.fetchone()["total"]


def get_all_budgets_status() -> list[dict]:
    """获取所有预算的状态（预算 vs 实际支出）

    Returns:
        预算状态列表，包含 budget, spent, remaining, percentage
    """
    budgets = list_budgets()
    results = []

    for budget in budgets:
        spent = get_budget_spent(budget["category"], budget["start_date"], budget["end_date"])
        remaining = budget["amount_cents"] - spent

        # 计算百分比
        if budget["amount_cents"] > 0:
            percentage = (spent / budget["amount_cents"]) * 100
        else:
            percentage = 0

        results.append({
            "id": budget["id"],
            "category": budget["category"],
            "period": budget["period"],
            "start_date": budget["start_date"],
            "end_date": budget["end_date"],
            "budget": budget["amount_cents"],
            "spent": spent,
            "remaining": remaining,
            "percentage": round(percentage, 2)
        })

    return results
