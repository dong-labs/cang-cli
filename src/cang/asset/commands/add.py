"""Asset add 命令 - 添加新资产"""

import typer
from cang.output.formatter import json_output, InvalidInputError, AlreadyExistsError
from cang.asset.repository import create_asset, ASSET_TYPES
from cang.db.utils import to_cents


@json_output
def add_asset(
    name: str = typer.Option(..., "--name", "-n", help="资产名称"),
    asset_type: str = typer.Option(..., "--type", "-t", help=f"资产类型: {', '.join(ASSET_TYPES)}"),
    amount: float | None = typer.Option(None, "--amount", "-a", help="持有数量"),
    currency: str = typer.Option("CNY", "--currency", "-c", help="货币代码，默认 CNY"),
    code: str | None = typer.Option(None, "--code", help="资产代码（如股票代码）"),
    value: float | None = typer.Option(None, "--value", "-v", help="当前市值（与 amount 二选一）"),
):
    """添加新资产

    可以指定持有数量（amount）或当前市值（value）。
    如果只指定 amount，则市值等于数量。
    """
    # 验证资产类型
    if asset_type not in ASSET_TYPES:
        raise InvalidInputError(
            f"Invalid asset type: {asset_type}. Must be one of: {', '.join(ASSET_TYPES)}"
        )

    # 处理金额
    amount_cents = None
    value_cents = 0

    if value is not None:
        value_cents = to_cents(value)
    elif amount is not None:
        amount_cents = to_cents(amount)
        value_cents = amount_cents
    else:
        raise InvalidInputError("Must specify either --amount or --value")

    asset = create_asset(
        name=name,
        asset_type=asset_type,
        amount=amount_cents,
        currency=currency,
        code=code
    )

    # 更新市值
    from cang.asset.repository import update_asset
    update_asset(asset["id"], value=value_cents)

    return {
        "asset": update_asset(asset["id"]),
        "message": "Asset created successfully"
    }
