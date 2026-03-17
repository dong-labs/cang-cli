# Cang CLI 测试策略

> 版本: v1.0
> 制定者: Qa
> 制定日期: 2026-03-15

---

## 1. 测试范围

### 1.1 模块划分

| 模块 | 测试类型 | 覆盖目标 |
|------|---------|----------|
| `db/` | 单元测试 | 90%+ |
| `output/` | 单元测试 | 90%+ |
| `fin/` | 单元 + 集成测试 | 80%+ |
| `asset/` | 单元 + 集成测试 | 80%+ |
| `invest/` | 单元 + 集成测试 | 80%+ |
| `budget/` | 单元 + 集成测试 | 80%+ |
| `cli.py` | 集成测试 | 70%+ |

### 1.2 不测试内容

- 第三方库内部逻辑 (Typer, sqlite3)
- Python 标准库功能
- 已由底层框架保证的功能

---

## 2. 测试框架

### 2.1 核心工具

- **pytest**: 测试运行器
- **pytest-cov**: 覆盖率报告
- **pytest-mock**: Mock 工具

### 2.2 目录结构

```
tests/
├── __init__.py
├── conftest.py                # 共享 fixtures
├── unit/                      # 单元测试
│   ├── db/
│   │   ├── test_connection.py
│   │   ├── test_schema.py
│   │   └── test_utils.py
│   ├── output/
│   │   └── test_formatter.py
│   ├── fin/
│   ├── asset/
│   ├── invest/
│   └── budget/
└── integration/               # 集成测试
    ├── test_fin_cli.py
    ├── test_asset_cli.py
    ├── test_invest_cli.py
    └── test_budget_cli.py
```

---

## 3. 测试 Fixtures

### 3.1 内存数据库 Fixture

```python
# conftest.py
import sqlite3
import pytest
from pathlib import Path

@pytest.fixture
def memory_db():
    """创建内存数据库，每个测试独立"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()
```

### 3.2 临时数据库文件 Fixture

```python
@pytest.fixture
def temp_db_file(tmp_path):
    """创建临时数据库文件"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    yield conn, db_path
    conn.close()
```

---

## 4. 测试用例规范

### 4.1 单元测试规范

每个函数需要覆盖的场景：
- 正常路径
- 边界条件
- 异常输入
- 错误处理

**示例结构：**

```python
class TestToCents:
    """测试 to_cents 函数"""

    def test_float_input(self):
        assert to_cents(29.9) == 2990

    def test_string_input(self):
        assert to_cents("29.9") == 2990

    def test_decimal_input(self):
        assert to_cents(Decimal("29.9")) == 2990

    def test_zero(self):
        assert to_cents(0) == 0

    def test_negative(self):
        assert to_cents(-10.5) == -1050

    def test_invalid_input(self):
        with pytest.raises(ValueError):
            to_cents("invalid")
```

### 4.2 集成测试规范

CLI 命令需要验证：
- JSON 输出格式正确
- 成功/失败标志正确
- 数据库状态正确
- 错误信息结构化

**示例结构：**

```python
def test_account_add(cli_runner, memory_db):
    """测试添加账户"""
    result = cli_runner.invoke(
        ["fin", "account", "add", "--name", "招商银行", "--type", "checking"]
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["success"] is True
    assert "account_id" in data["data"]
```

---

## 5. JSON 输出验证

### 5.1 成功响应格式

```json
{
  "success": true,
  "data": {
    // 具体数据
  }
}
```

### 5.2 失败响应格式

```json
{
  "success": false,
  "error": {
    "code": "ErrorCode",
    "message": "人类可读的错误信息"
  }
}
```

### 5.3 验证 Helper

```python
def assert_success_response(output):
    """断言成功响应"""
    data = json.loads(output)
    assert data["success"] is True
    assert "data" in data
    assert "error" not in data
    return data["data"]

def assert_error_response(output, expected_code=None):
    """断言错误响应"""
    data = json.loads(output)
    assert data["success"] is False
    assert "error" in data
    assert "data" not in data
    if expected_code:
        assert data["error"]["code"] == expected_code
    return data["error"]
```

---

## 6. 测试覆盖率

### 6.1 目标

- **整体覆盖率**: 80%+
- **核心模块** (db/, output/): 90%+
- **业务模块** (fin/, asset/, invest/, budget/): 80%+

### 6.2 生成覆盖率报告

```bash
pytest --cov=src/cang --cov-report=html --cov-report=term
```

### 6.3 CI 集成

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: pytest --cov=src/cang --cov-report=xml

- name: Check coverage
  run: |
    coverage=$(python -c "import xml.etree.ElementTree as ET; print(ET.parse('coverage.xml').getroot().attrib['line-rate'])")
    if (( $(echo "$coverage < 0.8" | bc -l) )); then
      exit 1
    fi
```

---

## 7. 测试运行

### 7.1 本地运行

```bash
# 运行所有测试
pytest

# 运行特定模块
pytest tests/unit/db/
pytest tests/integration/test_fin_cli.py

# 带覆盖率报告
pytest --cov=src/cang --cov-report=html

# 详细输出
pytest -v

# 只运行失败的测试
pytest --lf
```

### 7.2 并行运行

```bash
pytest -n auto  # 需要 pytest-xdist
```

---

## 8. 待编写的测试用例

### 8.1 db/ 模块

| 文件 | 函数 | 测试点 |
|------|------|--------|
| connection.py | get_db_path() | 目录不存在时创建、缓存 |
| connection.py | get_connection() | 单例、线程安全、row_factory |
| connection.py | close_connection() | 关闭后重新获取 |
| connection.py | get_cursor() | 事务提交、回滚 |
| schema.py | get_current_version() | 无版本、有版本 |
| schema.py | set_version() | 新版本、覆盖旧版本 |
| schema.py | create_meta_table() | 重复创建 |
| schema.py | migrate() | 全新安装、版本升级 |
| utils.py | to_cents() | 类型支持、边界值、异常 |
| utils.py | from_cents() | 格式化、负数 |
| utils.py | from_cents_decimal() | 精度保持 |

### 8.2 output/ 模块

| 文件 | 函数 | 测试点 |
|------|------|--------|
| formatter.py | output() | success=True/False、JSON 格式 |
| formatter.py | handle_error() | 异常类型、错误信息 |
| formatter.py | exception_handler() | 异常捕获 |

### 8.3 fin/ 模块

| 命令 | 测试点 |
|------|--------|
| fin init | 数据库创建、重复初始化 |
| account ls | 空列表、有数据 |
| account add | 参数验证、数据库插入 |
| account balance | 不存在账户、余额计算 |
| tx ls | 筛选条件、排序 |
| tx add | 金额转换、分类验证 |
| tx get | 存在/不存在 |
| tx update | 部分更新、全量更新 |
| tx delete | 存在/不存在 |
| transfer | 账户存在性、金额验证、原子性 |
| summary | 时间范围、分类汇总 |
| schema | 版本查询 |

---

## 9. 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-03-15 | 初始版本 |
