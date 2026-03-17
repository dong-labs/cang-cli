"""Cang CLI - 主入口

支持 python -m cang 运行
"""

import sys

import typer

from cang.cli import app, handle_error
from cang.output import error_from_exception, print_json


def main() -> None:
    """主入口函数

    捕获所有异常，通过 formatter 输出错误 JSON
    """
    try:
        app()
    except SystemExit:
        # Typer 的 Exit 信号，正常传递
        raise
    except Exception as e:
        # 其他异常，格式化为 JSON 输出
        print_json(error_from_exception(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
