"""Asset networth 命令 - 计算净资产"""

import typer
from cang.output.formatter import json_output
from cang.asset.repository import calculate_networth


@json_output
def networth_cmd(
    currency: str = typer.Option("CNY", "--currency", "-c", help="目标货币（预留）"),
):
    """计算净资产

    返回总净资产和按货币分组的资产汇总。
    """
    result = calculate_networth(target_currency=currency)

    return {
        "networth": result["networth"],
        "networth_cents": result["networth_cents"],
        "by_currency": result["by_currency"],
        "asset_count": result["asset_count"],
        "note": "汇率转换功能尚未实现，当前仅做简单汇总"
    }
