"""search 命令 - 搜索交易记录"""

import typer
from cang.output.formatter import json_output
from cang.fin.repository import list_transactions


@json_output
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(20, "--limit", "-l", help="返回数量"),
):
    """全文搜索交易记录

    搜索范围包括：备注、分类、标签
    """
    # 获取所有交易
    transactions = list_transactions(limit=None)

    # 搜索匹配
    query_lower = query.lower()
    filtered = [
        t for t in transactions
        if query_lower in (t.get("note") or "").lower()
        or query_lower in (t.get("category") or "").lower()
        or query_lower in (t.get("tags") or "").lower()
    ]

    # 限制数量
    results = filtered[:limit]

    return {
        "query": query,
        "total": len(filtered),
        "items": results
    }
