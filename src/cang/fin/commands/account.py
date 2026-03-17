"""Account 命令组 - 账户管理

命令:
- ls: 列出所有账户
- add: 添加新账户
- get: 获取账户详情
- balance: 查询账户余额
"""

import typer
from cang.output.formatter import json_output, AlreadyExistsError, NotFoundError, InvalidInputError
from cang.fin.repository import (
    list_accounts,
    get_account_by_id,
    get_account_by_name,
    create_account,
    get_account_balance,
)
from cang.db.utils import from_cents, format_currency

# 支持的账户类型
ACCOUNT_TYPES = ["cash", "bank", "alipay", "wechat", "credit"]

app = typer.Typer(help="账户管理")


@app.command(name="ls")
@json_output
def list_accounts_cmd():
    """列出所有账户"""
    accounts = list_accounts()
    return {"accounts": accounts}


@app.command(name="add")
@json_output
def add_account(
    name: str = typer.Option(..., "--name", "-n", help="账户名称"),
    account_type: str = typer.Option(..., "--type", "-t", help=f"账户类型: {', '.join(ACCOUNT_TYPES)}"),
    currency: str = typer.Option("CNY", "--currency", "-c", help="货币代码，默认 CNY"),
):
    """添加新账户

    如果账户名称已存在，返回错误。
    """
    # 验证账户类型
    if account_type not in ACCOUNT_TYPES:
        raise InvalidInputError(
            f"Invalid account type: {account_type}. Must be one of: {', '.join(ACCOUNT_TYPES)}"
        )

    # 检查是否已存在
    existing = get_account_by_name(name)
    if existing:
        raise AlreadyExistsError(f"Account '{name}' already exists")

    account = create_account(name, account_type, currency)
    return account


@app.command(name="get")
@json_output
def get_account(
    account_id: int = typer.Option(..., "--id", help="账户 ID"),
):
    """获取账户详情"""
    account = get_account_by_id(account_id)
    if not account:
        raise NotFoundError(f"Account with id {account_id} not found")

    return {"account": account}


@app.command(name="balance")
@json_output
def account_balance(
    account_id: int | None = typer.Option(None, "--account-id", "-a", help="账户 ID，不指定则返回所有账户余额"),
):
    """查询账户余额

    不指定账户时，返回所有账户的余额列表。
    """
    if account_id is None:
        # 返回所有账户余额
        accounts = list_accounts()
        balances = []
        for acc in accounts:
            balance_cents = get_account_balance(acc["id"])
            balances.append({
                "account_id": acc["id"],
                "account": acc["name"],
                "balance": from_cents(balance_cents),
                "formatted": format_currency(balance_cents, acc["currency"])
            })
        return {"balances": balances}

    # 返回指定账户余额
    account = get_account_by_id(account_id)
    if not account:
        raise NotFoundError(f"Account with id {account_id} not found")

    balance_cents = get_account_balance(account_id)

    return {
        "account_id": account["id"],
        "account": account["name"],
        "balance": from_cents(balance_cents),
        "formatted": format_currency(balance_cents, account["currency"])
    }
