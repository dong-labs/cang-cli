"""tags 命令 - 标签管理"""

import typer
from cang.output.formatter import json_output
from cang.fin.repository import list_transactions


@json_output
def list_tags():
    """列出所有标签及使用数量"""
    # 获取所有交易
    transactions = list_transactions(limit=None)

    # 统计标签
    tag_counter = {}
    for t in transactions:
        tags = t.get("tags") or ""
        if tags:
            for tag in tags.split(","):
                tag = tag.strip()
                if tag:
                    tag_counter[tag] = tag_counter.get(tag, 0) + 1

    # 按数量排序
    sorted_tags = sorted(tag_counter.items(), key=lambda x: x[1], reverse=True)
    tags_list = [{"tag": tag, "count": count} for tag, count in sorted_tags]

    return {
        "total_tags": len(tag_counter),
        "total_usages": sum(tag_counter.values()),
        "tags": tags_list
    }
