"""Cang CLI 常量定义"""

from pathlib import Path

# 数据库路径 - 统一放在 ~/.dong/ 下
DB_DIR = Path.home() / ".dong" / "cang"
DB_PATH = DB_DIR / "cang.db"

# Schema 版本
SCHEMA_VERSION = "2"

# 支持的账户类型
ACCOUNT_TYPES = ["cash", "bank", "alipay", "wechat", "credit"]

# 支持的货币
CURRENCIES = ["CNY", "USD", "EUR", "JPY", "HKD"]

# 支持的周期
PERIODS = ["today", "week", "month", "quarter", "year"]

# 预算周期
BUDGET_PERIODS = ["week", "month", "quarter", "year"]

# 投资类型
INVEST_TYPES = ["stock", "fund", "bond", "crypto"]

# 资产类型
ASSET_TYPES = ["cash", "bank", "alipay", "wechat", "stock", "fund", "house", "car", "debt"]
