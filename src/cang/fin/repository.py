"""Fin 模块数据访问层

职责:
- 封装所有数据库操作
- 提供类型化的数据访问接口
- 处理金额转换 (分 <-> 元)

注意: 此模块使用 db/connection.py 提供的 get_cursor() 进行数据库操作。
"""

from cang.db.connection import get_cursor


# ============================================================================
# Account 相关操作
# ============================================================================

def list_accounts() -> list[dict]:
    """列出所有账户

    Returns:
        账户列表，每个账户包含 id, name, type, currency, created_at
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM accounts ORDER BY id")
        return [dict(row) for row in cur.fetchall()]


def get_account_by_id(account_id: int) -> dict | None:
    """根据 ID 获取账户

    Args:
        account_id: 账户 ID

    Returns:
        账户信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_account_by_name(name: str) -> dict | None:
    """根据名称获取账户

    Args:
        name: 账户名称

    Returns:
        账户信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM accounts WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_account(name: str, account_type: str, currency: str = "CNY") -> dict:
    """创建新账户

    Args:
        name: 账户名称
        account_type: 账户类型
        currency: 货币代码，默认 CNY

    Returns:
        新创建的账户信息
    """
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO accounts (name, type, currency) VALUES (?, ?, ?)",
            (name, account_type, currency)
        )
        return get_account_by_id(cur.lastrowid)


# ============================================================================
# Transaction 相关操作
# ============================================================================

def list_transactions(
    limit: int | None = None,
    account_id: int | None = None,
    category: str | None = None
) -> list[dict]:
    """列出交易记录

    Args:
        limit: 限制返回数量
        account_id: 筛选指定账户
        category: 筛选指定分类

    Returns:
        交易列表
    """
    query = "SELECT * FROM transactions"
    params = []

    conditions = []
    if account_id:
        conditions.append("account_id = ?")
        params.append(account_id)
    if category:
        conditions.append("category = ?")
        params.append(category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date DESC, id DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def get_transaction_by_id(tx_id: int) -> dict | None:
    """根据 ID 获取交易

    Args:
        tx_id: 交易 ID

    Returns:
        交易信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_transaction(
    date: str,
    amount_cents: int,
    account_id: int,
    category: str | None = None,
    note: str | None = None,
    tags: str | None = None
) -> dict:
    """创建新交易

    Args:
        date: 日期字符串 (YYYY-MM-DD)
        amount_cents: 金额（分）
        account_id: 账户 ID
        category: 分类
        note: 备注
        tags: 标签（逗号分隔）

    Returns:
        新创建的交易信息
    """
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO transactions (date, amount_cents, account_id, category, note, tags)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (date, amount_cents, account_id, category, note, tags or "")
        )
        return get_transaction_by_id(cur.lastrowid)


# 定义允许更新的字段白名单（防止 SQL 注入）
_UPDATABLE_TX_FIELDS = frozenset({
    "date", "amount_cents", "account_id", "category", "note", "tags"
})


def _build_update_sql(fields: set[str]) -> str:
    """安全地构建 UPDATE SQL 语句

    使用字段白名单确保只有预定义的字段可以被更新，
    防止通过用户输入注入恶意 SQL。
    字段按固定顺序排序，确保与参数列表顺序一致。

    Args:
        fields: 要更新的字段集合

    Returns:
        str: SET 子句，如 "date = ?, amount_cents = ?"

    Raises:
        ValueError: 如果字段不在白名单中
    """
    # 验证所有字段都在白名单中
    invalid_fields = fields - _UPDATABLE_TX_FIELDS
    if invalid_fields:
        raise ValueError(
            f"Invalid transaction fields: {invalid_fields}. "
            f"Allowed fields: {_UPDATABLE_TX_FIELDS}"
        )

    # 安全地构建 SET 子句（字段名来自白名单，值使用参数化查询）
    # 对字段排序确保顺序一致
    return ", ".join(f"{field} = ?" for field in sorted(fields))


def update_transaction(
    tx_id: int,
    date: str | None = None,
    amount_cents: int | None = None,
    account_id: int | None = None,
    category: str | None = None,
    note: str | None = None,
    tags: str | None = None
) -> dict | None:
    """更新交易

    Args:
        tx_id: 交易 ID
        date: 新日期
        amount_cents: 新金额（分）
        account_id: 新账户 ID
        category: 新分类
        note: 新备注
        tags: 新标签

    Returns:
        更新后的交易信息，如果交易不存在返回 None
    """
    # 收集要更新的字段和对应的值
    fields_to_update = set()
    params = []

    if date is not None:
        fields_to_update.add("date")
        params.append(date)
    if amount_cents is not None:
        fields_to_update.add("amount_cents")
        params.append(amount_cents)
    if account_id is not None:
        fields_to_update.add("account_id")
        params.append(account_id)
    if category is not None:
        fields_to_update.add("category")
        params.append(category)
    if note is not None:
        fields_to_update.add("note")
        params.append(note)
    if tags is not None:
        fields_to_update.add("tags")
        params.append(tags)

    if not fields_to_update:
        return get_transaction_by_id(tx_id)

    # 使用安全的 SQL 构建函数
    set_clause = _build_update_sql(fields_to_update)
    params.append(tx_id)

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE transactions SET {set_clause} WHERE id = ?",
            params
        )
        return get_transaction_by_id(tx_id)


def delete_transaction(tx_id: int) -> bool:
    """删除交易

    Args:
        tx_id: 交易 ID

    Returns:
        是否成功删除
    """
    with get_cursor() as cur:
        cur.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        return cur.rowcount > 0


def get_account_balance(account_id: int) -> int:
    """获取账户余额

    Args:
        account_id: 账户 ID

    Returns:
        余额（分）
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(amount_cents), 0) FROM transactions WHERE account_id = ?",
            (account_id,)
        )
        return cur.fetchone()[0]


# ============================================================================
# Category 相关操作
# ============================================================================

def list_categories() -> list[dict]:
    """列出所有分类

    Returns:
        分类列表
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM categories ORDER BY id")
        return [dict(row) for row in cur.fetchall()]


def get_category_by_id(category_id: int) -> dict | None:
    """根据 ID 获取分类

    Args:
        category_id: 分类 ID

    Returns:
        分类信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_category_by_name(name: str) -> dict | None:
    """根据名称获取分类

    Args:
        name: 分类名称

    Returns:
        分类信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM categories WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_category(name: str) -> dict:
    """创建新分类

    Args:
        name: 分类名称

    Returns:
        新创建的分类信息
    """
    with get_cursor() as cur:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        return get_category_by_id(cur.lastrowid)


# ============================================================================
# Transfer 相关操作
# ============================================================================

def create_transfer(
    from_account_id: int,
    to_account_id: int,
    amount_cents: int,
    date: str,
    fee_cents: int = 0,
    note: str | None = None
) -> dict:
    """创建转账记录

    Args:
        from_account_id: 转出账户 ID
        to_account_id: 转入账户 ID
        amount_cents: 转账金额（分）
        date: 日期字符串 (YYYY-MM-DD)
        fee_cents: 手续费（分）
        note: 备注

    Returns:
        新创建的转账信息
    """
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO transfers (from_account_id, to_account_id, amount_cents, fee_cents, date, note)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (from_account_id, to_account_id, amount_cents, fee_cents, date, note)
        )
        return get_transfer_by_id(cur.lastrowid)


def get_transfer_by_id(transfer_id: int) -> dict | None:
    """根据 ID 获取转账

    Args:
        transfer_id: 转账 ID

    Returns:
        转账信息，如果不存在返回 None
    """
    with get_cursor() as cur:
        cur.execute("SELECT * FROM transfers WHERE id = ?", (transfer_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def list_transfers(limit: int | None = None) -> list[dict]:
    """列出转账记录

    Args:
        limit: 限制返回数量

    Returns:
        转账列表
    """
    query = "SELECT * FROM transfers ORDER BY date DESC, id DESC"
    if limit:
        query += " LIMIT ?"
        with get_cursor() as cur:
            cur.execute(query, [limit])
            return [dict(row) for row in cur.fetchall()]
    else:
        with get_cursor() as cur:
            cur.execute(query)
            return [dict(row) for row in cur.fetchall()]


# ============================================================================
# Summary 相关操作
# ============================================================================

def get_transaction_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    group_by: str = "category"
) -> list[dict]:
    """获取交易汇总

    Args:
        start_date: 开始日期
        end_date: 结束日期
        group_by: 分组方式 (category, account, date)

    Returns:
        汇总列表
    """
    conditions = []
    params = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    if group_by == "category":
        query = f"""
            SELECT category, SUM(amount_cents) as total, COUNT(*) as count
            FROM transactions
            {where_clause}
            GROUP BY category
            ORDER BY total DESC
        """
    elif group_by == "account":
        query = f"""
            SELECT a.name as account_name, SUM(t.amount_cents) as total, COUNT(*) as count
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            {where_clause}
            GROUP BY t.account_id
            ORDER BY total DESC
        """
    elif group_by == "date":
        query = f"""
            SELECT date, SUM(amount_cents) as total, COUNT(*) as count
            FROM transactions
            {where_clause}
            GROUP BY date
            ORDER BY date DESC
        """
    else:
        raise ValueError(f"Invalid group_by: {group_by}")

    with get_cursor() as cur:
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
