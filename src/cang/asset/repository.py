"""Asset 模块数据访问层

职责:
- 封装所有资产相关的数据库操作
- 提供类型化的数据访问接口
- 处理金额转换和净资产计算
"""

from cang.db.connection import get_cursor
from cang.db.utils import from_cents


# ============================================================================
# 字段白名单（防止 SQL 注入）
# ============================================================================

# 定义允许更新的资产字段白名单
_UPDATABLE_ASSET_FIELDS = frozenset({
    "amount_cents", "value_cents"
})


def _build_asset_update_sql(fields: set[str]) -> str:
    """安全地构建资产 UPDATE SQL 语句

    使用字段白名单确保只有预定义的字段可以被更新。
    字段按固定顺序排序，确保与参数列表顺序一致。

    Args:
        fields: 要更新的字段集合

    Returns:
        str: SET 子句，如 "amount_cents = ?, value_cents = ?"

    Raises:
        ValueError: 如果字段不在白名单中
    """
    invalid_fields = fields - _UPDATABLE_ASSET_FIELDS
    if invalid_fields:
        raise ValueError(
            f"Invalid asset fields: {invalid_fields}. "
            f"Allowed fields: {_UPDATABLE_ASSET_FIELDS}"
        )

    # 对字段排序确保顺序一致
    return ", ".join(f"{field} = ?" for field in sorted(fields))


# ============================================================================
# Asset 类型常量
# ============================================================================

# 支持的资产类型
ASSET_TYPES = [
    "cash",          # 现金
    "bank",          # 银行存款
    "stock",         # 股票
    "fund",          # 基金
    "bond",          # 债券
    "crypto",        # 加密货币
    "real_estate",   # 房产
    "vehicle",       # 车辆
    "gold",          # 黄金
    "other",         # 其他
]


# ============================================================================
# Asset 相关操作
# ============================================================================

def list_assets(
    asset_type: str | None = None,
    currency: str | None = None
) -> list[dict]:
    """列出所有资产

    Args:
        asset_type: 筛选指定类型
        currency: 筛选指定货币

    Returns:
        资产列表
    """
    query = "SELECT * FROM assets"
    params = []
    conditions = []

    if asset_type:
        conditions.append("type = ?")
        params.append(asset_type)
    if currency:
        conditions.append("currency = ?")
        params.append(currency)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id"

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_asset_by_id(asset_id: int) -> dict | None:
    """根据 ID 获取资产

    Args:
        asset_id: 资产 ID

    Returns:
        资产信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_asset(
    name: str,
    asset_type: str,
    amount: int | None = None,
    currency: str = "CNY",
    code: str | None = None
) -> dict:
    """创建新资产

    Args:
        name: 资产名称
        asset_type: 资产类型
        amount: 持有数量（以分为单位存储）
        currency: 货币代码
        code: 资产代码（如股票代码）

    Returns:
        新创建的资产信息
    """
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO assets (name, type, amount_cents, currency, code)
               VALUES (?, ?, ?, ?, ?)""",
            (name, asset_type, amount, currency, code)
        )
        return get_asset_by_id(cur.lastrowid)


def update_asset(
    asset_id: int,
    amount: int | None = None,
    value: int | None = None
) -> dict | None:
    """更新资产

    Args:
        asset_id: 资产 ID
        amount: 新的持有数量（分）
        value: 新的市值（分）

    Returns:
        更新后的资产信息，如果资产不存在返回 None
    """
    # 收集要更新的字段和对应的值
    fields_to_update = set()
    params = []

    if amount is not None:
        fields_to_update.add("amount_cents")
        params.append(amount)
    if value is not None:
        fields_to_update.add("value_cents")
        params.append(value)

    if not fields_to_update:
        return get_asset_by_id(asset_id)

    # 使用安全的 SQL 构建函数
    set_clause = _build_asset_update_sql(fields_to_update)
    params.append(asset_id)

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE assets SET {set_clause} WHERE id = ?",
            params
        )
        return get_asset_by_id(asset_id)


def delete_asset(asset_id: int) -> bool:
    """删除资产

    Args:
        asset_id: 资产 ID

    Returns:
        是否成功删除
    """
    with get_cursor() as cur:
        cur.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        return cur.rowcount > 0


def calculate_networth(target_currency: str = "CNY") -> dict:
    """计算净资产

    按货币分组计算总资产，返回总净资产。

    注意：当前版本仅做简单汇总，不支持汇率转换。
    未来需要扩展汇率转换功能。

    Args:
        target_currency: 目标货币（预留，当前未使用）

    Returns:
        净资产信息
    """
    # 获取所有资产
    assets = list_assets()

    # 按货币分组汇总
    by_currency: dict[str, int] = {}
    total_cents = 0

    for asset in assets:
        currency = asset["currency"]
        value_cents = asset["value_cents"]

        if currency not in by_currency:
            by_currency[currency] = 0
        by_currency[currency] += value_cents
        total_cents += value_cents

    return {
        "networth": from_cents(total_cents),
        "networth_cents": total_cents,
        "by_currency": {
            curr: from_cents(amount)
            for curr, amount in by_currency.items()
        },
        "by_currency_cents": by_currency,
        "asset_count": len(assets),
    }


def get_asset_schema() -> dict:
    """获取资产表结构信息

    Returns:
        表结构信息
    """
    return {
        "table": "assets",
        "columns": {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "type": "TEXT NOT NULL",
            "amount_cents": "INTEGER",
            "value_cents": "INTEGER NOT NULL DEFAULT 0",
            "currency": "TEXT DEFAULT 'CNY'",
            "code": "TEXT",
            "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
        },
        "asset_types": ASSET_TYPES,
    }
