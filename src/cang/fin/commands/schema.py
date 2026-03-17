"""Schema 命令 - 显示命令结构和使用说明

命令:
- schema: 显示命令结构
"""

import typer
from cang.output.formatter import json_output, NotFoundError

app = typer.Typer(help="命令结构说明")


# 命令结构定义
_COMMAND_SCHEMA = {
    "module": "fin",
    "description": "财务流动 - 钱怎么花的？",
    "commands": {
        "init": {
            "description": "初始化 fin 模块数据库",
            "usage": "cang fin init"
        },
        "schema": {
            "description": "显示命令结构和使用说明",
            "usage": "cang fin schema [command_path]",
            "examples": [
                "cang fin schema",
                "cang fin schema account",
                "cang fin schema account add"
            ]
        },
        "account": {
            "description": "账户管理",
            "usage": "cang fin account <command>",
            "commands": {
                "ls": {
                    "description": "列出所有账户",
                    "usage": "cang fin account ls",
                    "returns": '{"accounts": [...], "count": N}'
                },
                "add": {
                    "description": "添加新账户",
                    "usage": "cang fin account add NAME --type TYPE [--currency CURRENCY]",
                    "parameters": {
                        "name": "账户名称 (必填)",
                        "--type, -t": "账户类型，如: cash, bank, credit (必填)",
                        "--currency, -c": "货币代码，默认: CNY (可选)"
                    },
                    "returns": '{"account": {...}, "message": "..."}'
                },
                "get": {
                    "description": "获取账户详情",
                    "usage": "cang fin account get [ID] [--name NAME]",
                    "parameters": {
                        "id": "账户 ID (可选)",
                        "--name, -n": "账户名称 (可选)"
                    },
                    "note": "id 和 --name 必须提供其中一个",
                    "returns": '{"account": {...}}'
                },
                "balance": {
                    "description": "查询账户余额",
                    "usage": "cang fin account balance [ID] [--name NAME]",
                    "parameters": {
                        "id": "账户 ID (可选)",
                        "--name, -n": "账户名称 (可选)"
                    },
                    "note": "id 和 --name 必须提供其中一个",
                    "returns": '{"account_id": N, "account_name": "...", "balance_cents": N, "balance": "...", "formatted": "..."}'
                }
            }
        },
        "tx": {
            "description": "交易管理",
            "usage": "cang fin tx <command>",
            "commands": {
                "ls": {
                    "description": "列出交易记录",
                    "usage": "cang fin tx ls [--limit N] [--account ID] [--category NAME]",
                    "parameters": {
                        "--limit, -l": "限制返回数量 (可选)",
                        "--account, -a": "按账户 ID 筛选 (可选)",
                        "--category, -c": "按分类筛选 (可选)"
                    },
                    "returns": '{"transactions": [...], "count": N}'
                },
                "add": {
                    "description": "添加新交易",
                    "usage": "cang fin tx add AMOUNT --account ID [--date DATE] [--category NAME] [--note NOTE]",
                    "parameters": {
                        "amount": "金额，正数为收入，负数为支出 (必填)",
                        "--account, -a": "账户 ID (必填)",
                        "--date, -d": "日期 YYYY-MM-DD，默认今天 (可选)",
                        "--category, -c": "分类 (可选)",
                        "--note, -n": "备注 (可选)"
                    },
                    "returns": '{"transaction": {...}, "message": "..."}'
                },
                "get": {
                    "description": "获取交易详情",
                    "usage": "cang fin tx get ID",
                    "parameters": {
                        "id": "交易 ID (必填)"
                    },
                    "returns": '{"transaction": {...}}'
                },
                "update": {
                    "description": "更新交易",
                    "usage": "cang fin tx update ID [--amount N] [--account ID] [--date DATE] [--category NAME] [--note NOTE]",
                    "parameters": {
                        "id": "交易 ID (必填)",
                        "--amount": "新金额 (可选)",
                        "--account, -a": "新账户 ID (可选)",
                        "--date, -d": "新日期 (可选)",
                        "--category, -c": "新分类 (可选)",
                        "--note, -n": "新备注 (可选)"
                    },
                    "note": "只更新提供的字段",
                    "returns": '{"transaction": {...}, "message": "..."}'
                },
                "delete": {
                    "description": "删除交易",
                    "usage": "cang fin tx delete ID",
                    "parameters": {
                        "id": "交易 ID (必填)"
                    },
                    "returns": '{"message": "...", "id": N}'
                },
                "summary": {
                    "description": "交易汇总统计",
                    "usage": "cang fin tx summary [--start DATE] [--end DATE] [--group GROUP]",
                    "parameters": {
                        "--start, -s": "开始日期 YYYY-MM-DD (可选)",
                        "--end, -e": "结束日期 YYYY-MM-DD (可选)",
                        "--group, -g": "分组方式: category|account|date，默认 category (可选)"
                    },
                    "returns": '{"summary": [...], "group_by": "...", "count": N}'
                }
            }
        },
        "category": {
            "description": "分类管理",
            "usage": "cang fin category <command>",
            "commands": {
                "ls": {
                    "description": "列出所有分类",
                    "usage": "cang fin category ls",
                    "returns": '{"categories": [...]}'
                },
                "add": {
                    "description": "添加新分类",
                    "usage": "cang fin category add NAME",
                    "parameters": {
                        "name": "分类名称 (必填)"
                    },
                    "returns": '{"category": {...}, "message": "..."}'
                }
            }
        },
        "transfer": {
            "description": "转账管理",
            "usage": "cang fin transfer <command>",
            "commands": {
                "add": {
                    "description": "记录转账",
                    "usage": "cang fin transfer add AMOUNT --from ID --to ID [--date DATE] [--fee FEE] [--note NOTE]",
                    "parameters": {
                        "amount": "转账金额 (必填)",
                        "--from, -f": "转出账户 ID (必填)",
                        "--to, -t": "转入账户 ID (必填)",
                        "--date, -d": "日期 YYYY-MM-DD，默认今天 (可选)",
                        "--fee": "手续费，默认 0 (可选)",
                        "--note, -n": "备注 (可选)"
                    },
                    "returns": '{"transfer": {...}, "message": "..."}'
                },
                "ls": {
                    "description": "列出转账记录",
                    "usage": "cang fin transfer ls [--limit N]",
                    "parameters": {
                        "--limit, -l": "限制返回数量 (可选)"
                    },
                    "returns": '{"transfers": [...], "count": N}'
                }
            }
        }
    }
}


def _resolve_path(parts: list[str], commands: dict) -> dict | None:
    """递归解析命令路径

    Args:
        parts: 剩余的路径片段
        commands: 当前层级的 commands 字典

    Returns:
        解析到的命令结构，或 None
    """
    if not parts:
        return None

    part = parts[0]

    if part not in commands:
        return None

    item = commands[part]

    # 如果这是最后一个部分，返回当前项
    if len(parts) == 1:
        return item

    # 如果有子命令，继续深入
    if isinstance(item, dict) and "commands" in item:
        return _resolve_path(parts[1:], item["commands"])

    # 没有更多子命令但路径还有剩余，不匹配
    return None


@app.command(name="schema")
@json_output
def schema_cmd(
    command_path: str = typer.Argument(
        None,
        help="命令路径，如 'account add' 或 'tx ls'"
    )
):
    """显示命令结构和使用说明

    不带参数时返回整个 fin 模块的命令结构。
    带参数时返回指定命令的详细说明。

    Examples:
        cang fin schema                    # 显示所有命令
        cang fin schema account            # 显示 account 子命令组
        cang fin schema account add        # 显示 account add 详情
        cang fin schema tx ls              # 显示 tx ls 详情
    """
    if command_path is None:
        # 返回完整命令结构
        return _COMMAND_SCHEMA

    # 解析命令路径
    path_parts = command_path.strip().split()
    result = _resolve_path(path_parts, _COMMAND_SCHEMA["commands"])

    if result is None:
        raise NotFoundError(f"Command path '{command_path}' not found. Try 'cang fin schema' to see all commands.")

    # 添加路径信息
    if isinstance(result, dict):
        result = dict(result)  # 复制避免修改原数据
        result["_command_path"] = " ".join(path_parts)

    return result
