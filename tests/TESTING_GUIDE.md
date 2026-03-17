# Cang CLI 测试指南

> 版本: v1.0
> 最后更新: 2026-03-15

---

## 一、测试架构

### 1.1 目录结构

```
tests/
├── __init__.py
├── conftest.py              # 共享 fixtures
├── TESTING_GUIDE.md         # 本文档
├── helpers/                 # 测试辅助函数
│   └── __init__.py
├── factories/               # 测试数据工厂
│   └── __init__.py
├── unit/                    # 单元测试
│   ├── db/
│   ├── output/
│   ├── fin/
│   ├── asset/
│   ├── invest/
│   └── budget/
└── integration/             # 集成测试
    ├── test_fin_cli.py
    ├── test_asset_cli.py
    ├── test_invest_cli.py
    └── test_budget_cli.py
```

### 1.2 测试分层

| 层级 | 范围 | 目标覆盖率 |
|------|------|-----------|
| **单元测试** | 单个函数/方法 | 90%+ |
| **集成测试** | CLI 命令 | 80%+ |

---

## 二、使用 Fixtures

### 2.1 数据库 Fixtures

```python
# 空内存数据库（无 schema）
def test_something(memory_db):
    memory_db.execute("CREATE TABLE test ...")

# 带 schema 的内存数据库（空表）
def test_something(memory_db_with_full_schema):
    # 已创建所有表，但无数据
    pass

# 带示例数据的内存数据库
def test_something(memory_db_with_sample_data):
    # 已有示例账户、交易、资产等数据
    pass
```

### 2.2 数据工厂 Fixtures

```python
def test_with_factory(account_factory, transaction_factory):
    # 创建测试账户
    account = account_factory(name="测试账户", account_type="cash")
    
    # 创建测试交易
    tx = transaction_factory(
        account_id=account["id"],
        amount_cents=-2990,
        category="餐饮"
    )
```

### 2.3 使用数据工厂类

```python
from tests.factories import AccountFactory, TransactionFactory, AssetFactory

def test_with_factories():
    # 使用静态方法创建测试数据
    account = AccountFactory.bank(name="工商银行")
    expense = TransactionFactory.expense(amount=25, category="餐饮")
    stock = AssetFactory.stock(code="00700", quantity=100)
```

---

## 三、测试命名规范

### 3.1 文件命名

| 文件类型 | 命名规范 |
|----------|----------|
| 单元测试 | `test_<module>.py` |
| 集成测试 | `test_<module>_cli.py` |

### 3.2 测试类命名

```python
class TestListAccounts:        # 测试函数：list_accounts
class TestCreateTransaction:   # 测试函数：create_transaction
class TestUpdateAsset:         # 测试函数：update_asset
```

### 3.3 测试方法命名

```python
def test_<function>_<scenario>():
    """测试场景描述"""
    pass

# 示例
def test_list_accounts_empty():
    """测试：空账户列表"""
    
def test_list_accounts_with_data():
    """测试：有数据的账户列表"""
    
def test_create_account_duplicate_name():
    """测试：创建重名账户"""
```

---

## 四、测试覆盖场景

### 4.1 正常路径

```python
def test_create_account_success():
    """测试：成功创建账户"""
    result = create_account("测试账户", "cash")
    assert result["name"] == "测试账户"
    assert result["type"] == "cash"
```

### 4.2 边界条件

```python
def test_with_zero_amount():
    """测试：金额为 0"""
    
def test_with_negative_amount():
    """测试：负金额（支出）"""
    
def test_with_empty_string():
    """测试：空字符串输入"""
```

### 4.3 异常情况

```python
def test_account_not_found():
    """测试：账户不存在"""
    result = get_account_by_id(99999)
    assert result is None

def test_invalid_amount():
    """测试：无效金额"""
    with pytest.raises(ValueError):
        to_cents("invalid")
```

---

## 五、运行测试

### 5.1 运行全部测试

```bash
pytest
```

### 5.2 运行特定模块

```bash
pytest tests/unit/fin/
pytest tests/integration/test_fin_cli.py
```

### 5.3 运行特定测试

```bash
pytest tests/unit/fin/test_repository.py::TestCreateAccount
pytest -k "test_create_account"
```

### 5.4 带覆盖率报告

```bash
pytest --cov=src/cang --cov-report=html
pytest --cov=src/cang/fin --cov-report=term-missing
```

### 5.5 并行运行

```bash
pytest -n auto
```

---

## 六、测试编写模板

### 6.1 Repository 测试模板

```python
"""测试 fin.repository 模块"""

import pytest
from cang.fin.repository import list_accounts, create_account


class TestListAccounts:
    """测试 list_accounts 函数"""
    
    def test_empty_list(self, memory_db_with_full_schema):
        """测试：空账户列表"""
        result = list_accounts()
        assert result == []
    
    def test_with_accounts(self, memory_db_with_full_schema, account_factory):
        """测试：有数据的账户列表"""
        account_factory(name="账户1")
        account_factory(name="账户2")
        
        result = list_accounts()
        assert len(result) == 2
        assert result[0]["name"] == "账户1"


class TestCreateAccount:
    """测试 create_account 函数"""
    
    def test_success(self, memory_db_with_full_schema):
        """测试：成功创建账户"""
        result = create_account("测试账户", "cash")
        assert result["name"] == "测试账户"
        assert result["id"] > 0
    
    def test_duplicate_name(self, memory_db_with_full_schema, account_factory):
        """测试：重名账户"""
        account_factory(name="重复账户")
        
        with pytest.raises(Exception):  # 或具体的异常类型
            create_account("重复账户", "cash")
```

### 6.2 CLI 集成测试模板

```python
"""测试 fin CLI 命令"""

import json
from typer.testing import CliRunner
from cang.cli import app


class TestAccountCommands:
    """测试账户相关命令"""
    
    def test_account_ls_empty(self, cli_runner, memory_db_with_full_schema):
        """测试：列出空账户列表"""
        result = cli_runner.invoke(app, ["fin", "account", "ls"])
        assert result.exit_code == 0
        
        data = json.loads(result.output)
        assert data["success"] is True
        assert data["data"]["accounts"] == []
    
    def test_account_add(self, cli_runner, memory_db_with_full_schema):
        """测试：添加账户"""
        result = cli_runner.invoke(app, [
            "fin", "account", "add",
            "--name", "测试账户",
            "--type", "cash"
        ])
        assert result.exit_code == 0
        
        data = json.loads(result.output)
        assert data["success"] is True
        assert "account_id" in data["data"]
```

---

## 七、覆盖率目标

| 模块 | 目标覆盖率 | 当前覆盖率 |
|------|-----------|-----------|
| `db/` | 90% | 99% ✅ |
| `output/` | 90% | 100% ✅ |
| `fin/` | 80% | 0% ❌ |
| `asset/` | 80% | 0% ❌ |
| `invest/` | 80% | 0% ❌ |
| `budget/` | 80% | 0% ❌ |
| **整体** | **80%** | **11.56%** ❌ |

---

## 八、TDD 开发流程

1. **编写测试** - 先写测试，描述期望行为
2. **运行测试** - 确认测试失败（红色）
3. **编写代码** - 实现功能，使测试通过
4. **运行测试** - 确认测试通过（绿色）
5. **重构** - 优化代码，保持测试通过
6. **提交** - 测试和代码一起提交

---

**记住：测试是代码质量的第一道防线！**
