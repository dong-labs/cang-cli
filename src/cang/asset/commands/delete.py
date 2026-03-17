"""Asset delete 命令 - 删除资产"""

import typer
from cang.output.formatter import json_output, NotFoundError
from cang.asset.repository import get_asset_by_id, delete_asset as delete_asset_repo


@json_output
def delete_asset(
    asset_id: int = typer.Option(..., "--id", help="资产 ID"),
):
    """删除资产"""
    # 检查资产是否存在
    asset = get_asset_by_id(asset_id)
    if not asset:
        raise NotFoundError(f"Asset with id {asset_id} not found")

    deleted = delete_asset_repo(asset_id)

    return {
        "deleted": deleted,
        "asset_id": asset_id,
        "asset_name": asset["name"],
        "message": "Asset deleted successfully"
    }
