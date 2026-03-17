"""Asset get 命令 - 获取资产详情"""

import typer
from cang.output.formatter import json_output, NotFoundError
from cang.asset.repository import get_asset_by_id
from cang.db.utils import from_cents, format_currency


@json_output
def get_asset(
    asset_id: int = typer.Option(..., "--id", help="资产 ID"),
):
    """获取资产详情"""
    asset = get_asset_by_id(asset_id)
    if not asset:
        raise NotFoundError(f"Asset with id {asset_id} not found")

    # 添加格式化字段
    asset["amount_formatted"] = from_cents(asset["amount_cents"]) if asset["amount_cents"] else None
    asset["value_formatted"] = from_cents(asset["value_cents"])
    asset["value_display"] = format_currency(asset["value_cents"], asset["currency"])

    return {"asset": asset}
