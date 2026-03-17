"""Asset ls 命令 - 列出所有资产"""

import typer
from cang.output.formatter import json_output
from cang.asset.repository import list_assets, ASSET_TYPES


@json_output
def ls_assets(
    asset_type: str | None = typer.Option(None, "--type", "-t", help=f"按类型筛选: {', '.join(ASSET_TYPES)}"),
    currency: str | None = typer.Option(None, "--currency", "-c", help="按货币筛选 (如 CNY, USD)"),
):
    """列出所有资产

    支持按类型或货币筛选。
    """
    # 验证资产类型
    if asset_type and asset_type not in ASSET_TYPES:
        from cang.output.formatter import InvalidInputError
        raise InvalidInputError(
            f"Invalid asset type: {asset_type}. Must be one of: {', '.join(ASSET_TYPES)}"
        )

    assets = list_assets(asset_type=asset_type, currency=currency)
    return {
        "assets": assets,
        "count": len(assets)
    }
