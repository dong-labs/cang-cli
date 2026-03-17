"""Transfer 命令 - 账户转账

命令:
- transfer: 执行转账并记录
- ls: 列出转账记录
"""

import typer
from datetime import date
from cang.output.formatter import json_output, NotFoundError, InvalidInputError
from cang.fin.repository import (
    create_transfer,
    list_transfers,
    get_account_by_id,
    create_transaction,
)
from cang.db.utils import to_cents, from_cents

app = typer.Typer(help="转账管理")


@app.command(name="transfer")
@json_output
def transfer_cmd(
    from_account: int = typer.Option(..., "--from", "-f", help="转出账户 ID"),
    to_account: int = typer.Option(..., "--to", "-t", help="转入账户 ID"),
    amount: float = typer.Option(..., "--amount", help="转账金额"),
    fee: float = typer.Option(0, "--fee", help="手续费，默认 0"),
    tx_date: str | None = typer.Option(None, "--date", "-d", help="日期 (YYYY-MM-DD)，默认今天"),
    note: str | None = typer.Option(None, "--note", "-n", help="备注"),
):
    """执行账户转账

    转账会：
    1. 创建转账记录到 transfers 表
    2. 从 from_account 扣除转账金额和手续费（创建负向交易）
    3. 向 to_account 增加转账金额（创建正向交易）

    手续费从转出账户额外扣除。
    """
    # 验证转出账户
    from_acc = get_account_by_id(from_account)
    if not from_acc:
        raise NotFoundError(f"Source account with id {from_account} not found")

    # 验证转入账户
    to_acc = get_account_by_id(to_account)
    if not to_acc:
        raise NotFoundError(f"Destination account with id {to_account} not found")

    # 验证不是同一账户
    if from_account == to_account:
        raise InvalidInputError("Cannot transfer to the same account")

    # 验证金额
    if amount <= 0:
        raise InvalidInputError("Transfer amount must be positive")

    # 默认日期为今天
    if tx_date is None:
        tx_date = date.today().isoformat()

    # 转换金额为分
    amount_cents = to_cents(amount)
    fee_cents = to_cents(fee)

    # 1. 创建转账记录
    transfer = create_transfer(
        from_account_id=from_account,
        to_account_id=to_account,
        amount_cents=amount_cents,
        date=tx_date,
        fee_cents=fee_cents,
        note=note
    )

    # 2. 创建交易记录
    # 转出账户：扣除金额 + 手续费（负数）
    from_total = -(amount_cents + fee_cents)
    create_transaction(
        date=tx_date,
        amount_cents=from_total,
        account_id=from_account,
        category="转账",
        note=f"转账至 {to_acc['name']}" + (f" (手续费: {from_cents(fee_cents)})" if fee_cents > 0 else "")
    )

    # 转入账户：增加金额（正数）
    create_transaction(
        date=tx_date,
        amount_cents=amount_cents,
        account_id=to_account,
        category="转账",
        note=f"从 {from_acc['name']} 转入"
    )

    return {
        "id": transfer["id"],
        "from": f"{from_acc['name']} (ID:{from_account})",
        "to": f"{to_acc['name']} (ID:{to_account})",
        "amount": from_cents(amount_cents),
        "fee": from_cents(fee_cents),
        "date": tx_date,
        "total_deducted": from_cents(amount_cents + fee_cents)
    }


@app.command(name="ls")
@json_output
def list_transfer(
    limit: int | None = typer.Option(None, "--limit", "-l", help="限制数量")
):
    """列出转账记录

    按时间倒序排列，可限制返回数量。
    """
    transfers = list_transfers(limit=limit)
    return {"transfers": transfers, "count": len(transfers)}
