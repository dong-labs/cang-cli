"""统一的输出格式化 - 使用 dong-core

此模块保留作为兼容层，内部委托给 dong-core。
"""

# 从 dong-core 导入所有公共组件
from dong.output.formatter import json_output
from dong.errors.exceptions import (
    DongError,
    ValidationError,
    NotFoundError,
    ConflictError,
)

# 导出旧的类名作为别名，保持向后兼容
CangError = DongError
DatabaseError = DongError
InvalidInputError = ValidationError
AlreadyExistsError = ConflictError

__all__ = [
    "json_output",
    "DongError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    # 向后兼容的别名
    "CangError",
    "DatabaseError",
    "InvalidInputError",
    "AlreadyExistsError",
]
