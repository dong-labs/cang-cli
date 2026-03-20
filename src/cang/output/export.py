"""导出命令

导出财务数据为 JSON/CSV/Markdown 格式。
"""

import typer
from rich.console import Console
from dong.io import ExporterRegistry

from cang.exporter import CangExporter

console = Console()


def export(
    output: str = typer.Option("cang.json", "-o", "--output", help="输出文件"),
    format: str = typer.Option("json", "-f", "--format", help="格式: json/md"),
):
    """
    导出财务数据
    
    Examples:
        dong-cang export                    # 导出为 JSON
        dong-cang export -o cang.md -f md   # 导出为 Markdown
    """
    # 确保 exporter 已注册
    if not ExporterRegistry.get("cang"):
        ExporterRegistry.register(CangExporter())
    
    exporter = ExporterRegistry.get("cang")
    
    # 导出
    if format == "json":
        data = exporter.to_json()
    elif format in ["md", "markdown"]:
        data = exporter.to_markdown()
    else:
        console.print(f"❌ 不支持的格式: {format}", style="red")
        raise typer.Exit(1)
    
    # 写入文件
    with open(output, "w", encoding="utf-8") as f:
        f.write(data)
    
    # 统计
    all_data = exporter.fetch_all()
    total_count = sum(
        len(items) if isinstance(items, list) else 0 
        for items in all_data.values()
    )
    
    console.print(f"✅ 已导出 {total_count} 条财务数据到 {output}", style="green")
