"""数据库 Schema 定义和版本管理

职责:
- 定义 Schema 版本
- 创建所有必要的数据表
- 管理数据库版本升级
"""

from cang.db.connection import get_connection, get_cursor

# 当前 Schema 版本
SCHEMA_VERSION = "3"


# ============================================================================
# 表结构定义 (SQL)
# ============================================================================

# cang_meta 表 - 存储全局元数据（如 schema 版本）
_SQL_CREATE_META_TABLE = """
    CREATE TABLE IF NOT EXISTS cang_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
"""

# accounts 表 - 账户信息
_SQL_CREATE_ACCOUNTS_TABLE = """
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,
        currency TEXT DEFAULT 'CNY',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

# transactions 表 - 交易记录
_SQL_CREATE_TRANSACTIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount_cents INTEGER NOT NULL,
        account_id INTEGER REFERENCES accounts(id),
        category TEXT,
        note TEXT,
        tags TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

# categories 表 - 分类信息
_SQL_CREATE_CATEGORIES_TABLE = """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
"""

# transfers 表 - 转账记录
_SQL_CREATE_TRANSFERS_TABLE = """
    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_account_id INTEGER NOT NULL REFERENCES accounts(id),
        to_account_id INTEGER NOT NULL REFERENCES accounts(id),
        amount_cents INTEGER NOT NULL,
        fee_cents INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

# invest_transactions 表 - 投资交易记录
_SQL_CREATE_INVEST_TRANSACTIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS invest_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        symbol TEXT NOT NULL,
        type TEXT NOT NULL,
        price_cents INTEGER NOT NULL,
        quantity REAL NOT NULL,
        amount_cents INTEGER NOT NULL,
        fee_cents INTEGER DEFAULT 0,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

# budgets 表 - 预算设置
_SQL_CREATE_BUDGETS_TABLE = """
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount_cents INTEGER NOT NULL,
        period TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""

# assets 表 - 资产记录
_SQL_CREATE_ASSETS_TABLE = """
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        amount_cents INTEGER,
        value_cents INTEGER NOT NULL DEFAULT 0,
        currency TEXT DEFAULT 'CNY',
        code TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""


# ============================================================================
# Schema 版本管理
# ============================================================================

def get_schema_version() -> str | None:
    """获取当前数据库的 Schema 版本"""
    import sqlite3
    try:
        with get_cursor() as cur:
            cur.execute(
                "SELECT value FROM cang_meta WHERE key = 'schema_version'"
            )
            row = cur.fetchone()
            return row["value"] if row else None
    except sqlite3.OperationalError:
        return None


def set_schema_version(version: str) -> None:
    """设置 Schema 版本"""
    with get_cursor() as cur:
        cur.execute(
            "INSERT OR REPLACE INTO cang_meta (key, value) VALUES ('schema_version', ?)",
            (version,)
        )


# ============================================================================
# 表创建函数
# ============================================================================

def _create_meta_table() -> None:
    """创建 cang_meta 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_META_TABLE)


def _create_accounts_table() -> None:
    """创建 accounts 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_ACCOUNTS_TABLE)


def _create_transactions_table() -> None:
    """创建 transactions 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_TRANSACTIONS_TABLE)


def _create_categories_table() -> None:
    """创建 categories 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_CATEGORIES_TABLE)


def _create_transfers_table() -> None:
    """创建 transfers 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_TRANSFERS_TABLE)


def _create_invest_transactions_table() -> None:
    """创建 invest_transactions 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_INVEST_TRANSACTIONS_TABLE)


def _create_budgets_table() -> None:
    """创建 budgets 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_BUDGETS_TABLE)


def _create_assets_table() -> None:
    """创建 assets 表"""
    with get_cursor() as cur:
        cur.execute(_SQL_CREATE_ASSETS_TABLE)


# ============================================================================
# 数据库初始化
# ============================================================================

def init_database() -> None:
    """初始化数据库，创建所有必要表"""
    current_version = get_schema_version()

    if current_version is None:
        # 全新安装
        _create_meta_table()
        _create_accounts_table()
        _create_transactions_table()
        _create_categories_table()
        _create_transfers_table()
        _create_invest_transactions_table()
        _create_budgets_table()
        _create_assets_table()
        set_schema_version(SCHEMA_VERSION)
    elif current_version != SCHEMA_VERSION:
        # 版本差异，需要迁移
        _migrate_from_v2(current_version)


def _migrate_from_v2(old_version: str) -> None:
    """从 v2 迁移到 v3（添加 tags 字段）"""
    with get_cursor() as cur:
        # 添加 tags 字段到 transactions 表
        try:
            cur.execute("ALTER TABLE transactions ADD COLUMN tags TEXT DEFAULT ''")
        except Exception:
            pass  # 字段可能已存在

        # 创建 tags 索引
        cur.execute("CREATE INDEX IF NOT EXISTS idx_transactions_tags ON transactions(tags)")

        set_schema_version(SCHEMA_VERSION)


def is_initialized() -> bool:
    """检查数据库是否已初始化"""
    version = get_schema_version()
    return version is not None
