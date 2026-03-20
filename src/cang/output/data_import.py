"""导入命令

从 JSON 文件导入财务数据。
"""

import json
import typer
from rich.console import Console
from rich.table import Table
from dong.io import ImporterRegistry

from cang.importer import CangImporter

console = Console()


def import_data(
    file: str = typer.Option(..., "-f", "--file", help="导入文件"),
    merge: bool = typer.Option(False, "--merge", help="合并模式（不删除现有数据）"),
    dry_run: bool = typer.Option(False, "--dry-run", help="预览模式（不实际导入）"),
):
    """
    导入财务数据
    
    Examples:
        dong-cang import -f cang.json           # 替换导入
        dong-cang import -f cang.json --merge   # 合并导入
        dong-cang import -f cang.json --dry-run # 预览
    """
    # 确保 importer 已注册
    if not ImporterRegistry.get("cang"):
        ImporterRegistry.register(CangImporter())
    
    # 读取文件
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        console.print(f"❌ 文件不存在: {file}", style="red")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"❌ JSON 解析失败: {e}", style="red")
        raise typer.Exit(1)
    
    # 支持 { "cang": {...} } 格式
    if isinstance(data, dict) and "cang" in data:
        data = data["cang"]
    
    # 验证数据
    importer = ImporterRegistry.get("cang")
    is_valid, error_msg = importer.validate(data)
    
    if not is_valid:
        console.print(f"❌ 数据验证失败: {error_msg}", style="red")
        raise typer.Exit(1)
    
    # 预览模式
    if dry_run:
        console.print("\n📋 预览: 将导入以下数据\n")
        
        table = Table(show_header=True, header_style="bold")
        table.add_column("数据类型", style="cyan")
        table.add_column("数量")
        
        for key, items in data.items():
            if isinstance(items, list) and len(items) > 0:
                table.add_row(key, str(len(items)))
        
        console.print(table)
        return
    
    # 实际导入
    result = importer.import_data(data, merge=merge)
    
    # 显示结果
    mode = "合并" if merge else "替换"
    console.print(f"\n✅ 导入完成（{mode}模式）\n", style="green")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("数据类型")
    table.add_column("导入", style="green")
    table.add_column("跳过", style="yellow")
    
    for data_type, stats in result.items():
        imported = stats.get("imported", 0)
        skipped = stats.get("skipped", 0)
        table.add_row(data_type, str(imported), str(skipped))
    
    console.print(table)
