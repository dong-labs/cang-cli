"""Asset update 命令 - 更新资产"""

import typer
from cang.output.formatter import json_output, NotFoundError, InvalidInputError
from cang.asset.repository import get_asset_by_id, update_asset as update_asset_repo
from cang.db.utils import to_cents


@json_output
def update_asset_cmd(
    asset_id: int = typer.Option(..., "--id", help="资产 ID"),
    amount: float | None = typer.Option(None, "--amount", "-a", help="新的持有数量"),
    value: float | None = typer.Option(None, "--value", "-v", help="新的市值"),
):
    """更新资产

    可以更新持有数量或市值。至少需要指定一个。
    """
    # 验证输入
    if amount is None and value is None:
        raise InvalidInputError("Must specify at least one of --amount or --value")

    # 检查资产是否存在
    asset = get_asset_by_id(asset_id)
    if not asset:
        raise NotFoundError(f"Asset with id {asset_id} not found")

    # 转换参数
    amount_cents = to_cents(amount) if amount is not None else None
    value_cents = to_cents(value) if value is not None else None

    # 更新资产
    updated = update_asset_repo(asset_id, amount=amount_cents, value=value_cents)

    return {
        "asset": updated,
        "message": "Asset updated successfully"
    }
