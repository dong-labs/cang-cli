# Cang CLI - 基础架构设计

> 设计日期：2026-03-15
> 设计者：Gudong (Tech Lead)
> 版本：v1.0

---

## 1. 项目目录结构

```
cang-cli/
├── pyproject.toml                 # 项目配置 (PEP 517/518)
├── README.md
├── CLAUDE.md
│
├── src/
│   └── cang/                      # 主包
│       ├── __init__.py
│       ├── cli.py                 # Typer 主入口
│       ├── const.py               # 常量定义 (DB路径、版本号等)
│       │
│       ├── db/                    # 数据库层 (共享)
│       │   ├── __init__.py
│       │   ├── connection.py      # SQLite 连接管理
│       │   ├── schema.py          # Schema 版本管理
│       │   ├── migrations/        # 数据库迁移脚本
│       │   │   ├── __init__.py
│       │   │   └── v1_initial.py
│       │   └── utils.py           # 金额转换工具 (cents <-> 显示格式)
│       │
│       ├── models/                # 数据模型 (可选，用于类型提示)
│       │   ├── __init__.py
│       │   ├── fin.py
│       │   ├── asset.py
│       │   ├── invest.py
│       │   └── budget.py
│       │
│       ├── fin/                   # 模块 1: 财务流动
│       │   ├── __init__.py
│       │   ├── cli.py             # fin 命令定义
│       │   ├── commands/          # 命令实现
│       │   │   ├── __init__.py
│       │   │   ├── account.py
│       │   │   ├── tx.py
│       │   │   ├── transfer.py
│       │   │   ├── category.py
│       │   │   └── schema.py
│       │   └── queries.py         # SQL 查询封装
│       │
│       ├── asset/                 # 模块 2: 资产存量
│       │   ├── __init__.py
│       │   ├── cli.py
│       │   └── commands/
│       │       ├── __init__.py
│       │       └── ...
│       │
│       ├── invest/                # 模块 3: 投资记录
│       │   ├── __init__.py
│       │   ├── cli.py
│       │   └── commands/
│       │       ├── __init__.py
│       │       └── ...
│       │
│       └── budget/                # 模块 4: 预算管理
│           ├── __init__.py
│           ├── cli.py
│           └── commands/
│               ├── __init__.py
│               └── ...
│
├── tests/                         # 测试
│   ├── __init__.py
│   ├── conftest.py                # pytest fixtures
│   ├── unit/
│   └── integration/
│
└── .cang/                         # 数据目录 (运行时生成，不入库)
    └── cang.db
```

---

## 2. 数据库层设计

### 2.1 连接管理 (`db/connection.py`)

```python
"""
职责：
- 单例模式管理 SQLite 连接
- 确保数据库目录存在
- 提供上下文管理器
"""

import sqlite3
from pathlib import Path
from functools import lru_cache
from contextlib import contextmanager

DB_PATH = Path.home() / ".cang" / "cang.db"

@lru_cache(maxsize=1)
def get_db_path() -> Path:
    """获取数据库路径，确保目录存在"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DB_PATH

@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # 返回字典风格的结果
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """初始化数据库，创建所有表"""
    # 执行 schema 创建
    pass
```

### 2.2 Schema 版本管理 (`db/schema.py`)

```python
"""
职责：
- 管理数据库 schema 版本 (通过 cang_meta 表)
- 执行迁移
- 版本检查和升级
"""

SCHEMA_VERSION = "2"

def get_current_version() -> str:
    """获取当前数据库的 schema 版本"""
    with get_connection() as conn:
        cur = conn.execute("SELECT value FROM cang_meta WHERE key = 'schema_version'")
        row = cur.fetchone()
        return row["value"] if row else None

def set_version(version: str):
    """设置 schema 版本"""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cang_meta (key, value) VALUES ('schema_version', ?)",
            (version,)
        )

def create_meta_table():
    """创建 cang_meta 表"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cang_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

def migrate():
    """执行数据库迁移"""
    current = get_current_version()
    if current is None:
        # 全新安装
        create_meta_table()
        set_version(SCHEMA_VERSION)
        # 创建所有表
    elif current != SCHEMA_VERSION:
        # 执行迁移
        pass
```

### 2.3 金额转换工具 (`db/utils.py`)

```python
"""
职责：
- 用户友好格式 <-> 内部存储格式 (分)
- CLI 输入: "29.9" -> 2990
- CLI 输出: 2990 -> "29.90"
"""

from decimal import Decimal, ROUND_DOWN

def to_cents(amount: float | str | Decimal) -> int:
    """将金额转换为分 (整数)"""
    dec = Decimal(str(amount))
    return int(dec * 100)

def from_cents(cents: int) -> str:
    """将分转换为格式化的金额字符串"""
    return f"{cents / 100:.2f}"

def from_cents_decimal(cents: int) -> Decimal:
    """将分转换为 Decimal (用于计算)"""
    return Decimal(cents) / 100
```

---

## 3. CLI 框架层设计

### 3.1 统一 JSON 输出 (`cli.py`)

```python
"""
职责：
- 统一的 JSON 输出格式
- 统一的错误处理
- Typer 应用配置
"""

import typer
import json
from typing import Any
from pathlib import Path

app = typer.Typer(
    name="cang",
    help="仓咚咚 - 个人金融命令行工具 (AI Native)",
    no_args_is_help=True,
)

# 统一输出格式
def output(data: Any, success: bool = True):
    """输出 JSON 格式"""
    result = {"success": success}
    if success:
        result["data"] = data
    else:
        result["error"] = data
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))

# 统一错误处理
def handle_error(e: Exception):
    """处理异常并输出结构化错误"""
    error_info = {
        "code": type(e).__name__,
        "message": str(e)
    }
    output(error_info, success=False)
    raise typer.Exit(code=1)

# 全局异常处理器
def exception_handler(exc_type, exc_value, exc_traceback):
    handle_error(exc_value)
```

### 3.2 模块注册 (`cli.py`)

```python
# 注册四个模块
app.add_typer(fin.app, name="fin")
app.add_typer(asset.app, name="asset")
app.add_typer(invest.app, name="invest")
app.add_typer(budget.app, name="budget")
```

### 3.3 模块模板 (`fin/cli.py`)

```python
"""fin 模块 CLI 定义"""

import typer
from cang.cli import output, handle_error

app = typer.Typer(
    name="fin",
    help="财务流动 - 钱怎么花的？"
)

@app.command()
def init():
    """初始化 fin 模块数据库"""
    try:
        from cang.db.schema import init_fin_tables
        init_fin_tables()
        output({"message": "fin module initialized", "version": "1"})
    except Exception as e:
        handle_error(e)

@app.command()
def account_ls():
    """列出所有账户"""
    try:
        from cang.fin.queries import list_accounts
        accounts = list_accounts()
        output({"accounts": accounts})
    except Exception as e:
        handle_error(e)
```

---

## 4. 接口契约定义

每个模块需要实现以下接口 (以 fin 为例):

### 4.1 模块初始化接口

```python
# cang/fin/__init__.py
def init_module() -> None:
    """初始化模块数据表"""

def is_initialized() -> bool:
    """检查模块是否已初始化"""
```

### 4.2 命令接口规范

每个命令返回以下类型之一：

```python
# 成功响应
{
    "success": True,
    "data": {
        # 具体数据
    }
}

# 失败响应
{
    "success": False,
    "error": {
        "code": "ErrorCode",
        "message": "人类可读的错误信息"
    }
}
```

### 4.3 金额字段规范

所有金额相关字段必须：
1. 数据库存储为 `INTEGER`，单位为分
2. 字段名后缀 `_cents`
3. 输出时自动转换为格式化字符串

---

## 5. 配置文件

### 5.1 `pyproject.toml`

```toml
[project]
name = "cang-cli"
version = "0.1.0"
description = "仓咚咚 - 个人金融命令行工具 (AI Native)"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.12.0",
]

[project.scripts]
cang = "cang.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cang"]
```

---

## 6. 任务分派清单

### 阶段 1: 基础设施 (优先级最高)

| 任务 | 模块 | 负责人 | 依赖 |
|------|------|--------|------|
| 创建项目目录结构 | - | Gudong | - |
| 配置 pyproject.toml | - | Gudong | - |
| 实现数据库连接管理 | db | Backend Dev | - |
| 实现金额转换工具 | db | Backend Dev | - |
| 实现主 CLI 入口 | cli | Gudong | db |
| 实现 cang_meta 表和版本管理 | db | Backend Dev | - |

### 阶段 2: fin 模块 (第一个完整模块)

| 任务 | 负责人 | 依赖 |
|------|--------|------|
| 创建 accounts 表 | Backend Dev | db |
| 创建 transactions 表 | Backend Dev | db |
| 创建 categories 表 | Backend Dev | db |
| 创建 transfers 表 | Backend Dev | db |
| 实现 account ls/add/get/balance | Module Dev | accounts 表 |
| 实现 tx ls/add/get/update/delete | Module Dev | transactions 表 |
| 实现 transfer 命令 | Module Dev | transfers 表 |
| 实现 summary 命令 | Module Dev | transactions 表 |
| 实现 schema 命令 | Module Dev | - |

### 阶段 3: 其他模块

按开发顺序：budget → invest → asset

---

## 7. 设计决策记录

### 7.1 为什么用 SQLite 单文件？

- 零配置，开箱即用
- 适合个人数据量
- 易于备份和迁移
- Python 内置支持

### 7.2 为什么金额用整数？

- 浮点数精度问题 (0.1 + 0.2 != 0.3)
- 金融数据要求绝对精确
- CLI 层负责格式化，用户无感知

### 7.3 为什么模块代码互不依赖？

- 独立开发和测试
- 可以单独使用某个模块
- 避免循环依赖

### 7.4 为什么用 Typer？

- 类型提示友好
- 自动生成帮助信息
- Click 的现代替代品

---

## 8. 下一步行动

1. **批准此架构设计** - 提交给 team-lead
2. **创建基础骨架** - 建立目录和配置文件
3. **分派任务** - 按阶段分派给团队成员
4. **开始编码** - 从 db 层开始
