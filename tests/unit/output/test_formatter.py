"""测试输出格式化模块

测试 cang.output.formatter 模块的所有函数:
- success()
- error()
- error_from_exception()
- print_json()
- typer_echo()
- json_output 装饰器
- 异常类: CangError, DatabaseError, NotFoundError, InvalidInputError, AlreadyExistsError
"""

from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest

from cang.output.formatter import (
    # 错误码
    ErrorCode,
    # 异常类
    CangError,
    DatabaseError,
    NotFoundError,
    InvalidInputError,
    AlreadyExistsError,
    # 响应函数
    success,
    error,
    error_from_exception,
    # 输出函数
    print_json,
    typer_echo,
    # 装饰器
    json_output,
)


# =============================================================================
# ErrorCode 测试
# =============================================================================

class TestErrorCode:
    """测试错误码常量"""

    def test_database_error_code(self):
        """测试数据库错误码"""
        assert ErrorCode.DATABASE_ERROR == "DATABASE_ERROR"

    def test_not_found_code(self):
        """测试未找到错误码"""
        assert ErrorCode.NOT_FOUND == "NOT_FOUND"

    def test_invalid_input_code(self):
        """测试无效输入错误码"""
        assert ErrorCode.INVALID_INPUT == "INVALID_INPUT"

    def test_already_exists_code(self):
        """测试已存在错误码"""
        assert ErrorCode.ALREADY_EXISTS == "ALREADY_EXISTS"

    def test_permission_denied_code(self):
        """测试权限拒绝错误码"""
        assert ErrorCode.PERMISSION_DENIED == "PERMISSION_DENIED"

    def test_internal_error_code(self):
        """测试内部错误码"""
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"


# =============================================================================
# 异常类测试
# =============================================================================

class TestCangError:
    """测试基础异常类"""

    def test_creation(self):
        """测试创建异常"""
        exc = CangError("TEST_CODE", "Test message")
        assert exc.code == "TEST_CODE"
        assert exc.message == "Test message"
        assert str(exc) == "Test message"

    def test_is_exception(self):
        """测试是 Exception 的子类"""
        assert issubclass(CangError, Exception)
        assert isinstance(CangError("CODE", "msg"), Exception)


class TestDatabaseError:
    """测试数据库错误"""

    def test_creation(self):
        """测试创建数据库错误"""
        exc = DatabaseError("Connection failed")
        assert exc.code == ErrorCode.DATABASE_ERROR
        assert exc.message == "Connection failed"


class TestNotFoundError:
    """测试未找到错误"""

    def test_creation(self):
        """测试创建未找到错误"""
        exc = NotFoundError("Account not found")
        assert exc.code == ErrorCode.NOT_FOUND
        assert exc.message == "Account not found"


class TestInvalidInputError:
    """测试无效输入错误"""

    def test_creation(self):
        """测试创建无效输入错误"""
        exc = InvalidInputError("Invalid amount")
        assert exc.code == ErrorCode.INVALID_INPUT
        assert exc.message == "Invalid amount"


class TestAlreadyExistsError:
    """测试已存在错误"""

    def test_creation(self):
        """测试创建已存在错误"""
        exc = AlreadyExistsError("Account already exists")
        assert exc.code == ErrorCode.ALREADY_EXISTS
        assert exc.message == "Account already exists"


# =============================================================================
# success() 测试
# =============================================================================

class TestSuccess:
    """测试 success 函数"""

    def test_with_data(self):
        """测试带数据的成功响应"""
        result = success({"id": 1, "name": "test"})
        assert result == {
            "success": True,
            "data": {"id": 1, "name": "test"},
        }

    def test_with_none_data(self):
        """测试 data 为 None"""
        result = success(None)
        assert result == {
            "success": True,
            "data": None,
        }

    def test_with_string_data(self):
        """测试字符串数据"""
        result = success("OK")
        assert result == {
            "success": True,
            "data": "OK",
        }

    def test_with_list_data(self):
        """测试列表数据"""
        result = success([1, 2, 3])
        assert result == {
            "success": True,
            "data": [1, 2, 3],
        }

    def test_with_nested_data(self):
        """测试嵌套数据"""
        result = success({"accounts": [{"id": 1}, {"id": 2}]})
        assert result == {
            "success": True,
            "data": {"accounts": [{"id": 1}, {"id": 2}]},
        }


# =============================================================================
# error() 测试
# =============================================================================

class TestError:
    """测试 error 函数"""

    def test_basic_error(self):
        """测试基本错误响应"""
        result = error("NOT_FOUND", "Account not found")
        assert result == {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Account not found",
            },
        }

    def test_error_codes(self):
        """测试各种错误码"""
        result = error(ErrorCode.DATABASE_ERROR, "DB error")
        assert result["error"]["code"] == ErrorCode.DATABASE_ERROR

        result = error(ErrorCode.INVALID_INPUT, "Invalid input")
        assert result["error"]["code"] == ErrorCode.INVALID_INPUT

    def test_error_structure(self):
        """测试错误响应结构"""
        result = error("CODE", "Message")
        assert "success" in result
        assert "error" in result
        assert "data" not in result
        assert result["success"] is False
        assert "code" in result["error"]
        assert "message" in result["error"]


# =============================================================================
# error_from_exception() 测试
# =============================================================================

class TestErrorFromException:
    """测试 error_from_exception 函数"""

    def test_from_cang_error(self):
        """测试从 CangError 生成错误"""
        exc = NotFoundError("Account not found")
        result = error_from_exception(exc)
        assert result == {
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Account not found",
            },
        }

    def test_from_database_error(self):
        """测试从 DatabaseError 生成错误"""
        exc = DatabaseError("Connection failed")
        result = error_from_exception(exc)
        assert result["error"]["code"] == ErrorCode.DATABASE_ERROR

    def test_from_invalid_input_error(self):
        """测试从 InvalidInputError 生成错误"""
        exc = InvalidInputError("Invalid amount")
        result = error_from_exception(exc)
        assert result["error"]["code"] == ErrorCode.INVALID_INPUT

    def test_from_generic_exception(self):
        """测试从普通异常生成错误"""
        exc = ValueError("Some error")
        result = error_from_exception(exc)
        assert result["error"]["code"] == ErrorCode.INTERNAL_ERROR
        assert result["error"]["message"] == "Some error"

    def test_from_runtime_error(self):
        """测试从 RuntimeError 生成错误"""
        exc = RuntimeError("Runtime issue")
        result = error_from_exception(exc)
        assert result["error"]["code"] == ErrorCode.INTERNAL_ERROR


# =============================================================================
# typer_echo() 测试
# =============================================================================

class TestTyperEcho:
    """测试 typer_echo 函数"""

    def test_prints_message(self, capsys):
        """测试输出消息"""
        typer_echo("Hello, World!")
        captured = capsys.readouterr()
        assert captured.out == "Hello, World!"

    def test_prints_empty_string(self, capsys):
        """测试输出空字符串"""
        typer_echo("")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_no_newline_by_default(self, capsys):
        """测试默认不添加换行符"""
        typer_echo("test")
        captured = capsys.readouterr()
        assert captured.out == "test"


# =============================================================================
# print_json() 测试
# =============================================================================

class TestPrintJson:
    """测试 print_json 函数"""

    def test_prints_valid_json(self, capsys):
        """测试输出有效 JSON"""
        data = {"success": True, "data": {"id": 1}}
        print_json(data)
        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)
        assert result == data

    def test_json_indent(self, capsys):
        """测试 JSON 缩进格式"""
        data = {"success": True, "data": {"id": 1}}
        print_json(data)
        captured = capsys.readouterr()
        # 应该有缩进
        assert "  " in captured.out or "\n" in captured.out

    def test_ensure_ascii_false(self, capsys):
        """测试中文字符正确输出"""
        data = {"success": True, "data": {"name": "测试"}}
        print_json(data)
        captured = capsys.readouterr()
        # 应该包含中文字符，而不是转义序列
        assert "测试" in captured.out
        assert "\\u" not in captured.out


# =============================================================================
# json_output 装饰器测试
# =============================================================================

class TestJsonOutput:
    """测试 json_output 装饰器"""

    def test_successful_return(self, capsys):
        """测试正常返回值包装为成功响应"""
        @json_output
        def get_account():
            return {"id": 1, "name": "Cash"}

        get_account()
        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)
        assert result["success"] is True
        assert result["data"] == {"id": 1, "name": "Cash"}

    def test_cang_error_handling(self, capsys):
        """测试 CangError 包装为错误响应"""
        @json_output
        def get_account():
            raise NotFoundError("Account not found")

        get_account()
        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)
        assert result["success"] is False
        assert result["error"]["code"] == "NOT_FOUND"
        assert result["error"]["message"] == "Account not found"

    def test_generic_exception_handling(self, capsys):
        """测试普通异常包装为内部错误"""
        @json_output
        def divide_by_zero():
            return 1 / 0

        divide_by_zero()
        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)
        assert result["success"] is False
        assert result["error"]["code"] == "INTERNAL_ERROR"

    def test_with_arguments(self, capsys):
        """测试带参数的函数"""
        @json_output
        def add(a, b):
            return {"result": a + b}

        add(1, 2)
        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)
        assert result["data"]["result"] == 3

    def test_with_none_return(self, capsys):
        """测试返回 None"""
        @json_output
        def return_none():
            return None

        return_none()
        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)
        assert result["success"] is True
        assert result["data"] is None

    def test_preserves_function_name(self):
        """测试装饰器保留函数名和文档"""
        @json_output
        def my_function():
            """My function docstring"""
            return {"data": "value"}

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My function docstring"


# =============================================================================
# 集成测试
# =============================================================================

class TestFormatterIntegration:
    """输出格式化集成测试"""

    def test_complete_error_workflow(self, capsys):
        """测试完整的错误处理工作流"""
        @json_output
        def command():
            raise InvalidInputError("Invalid amount: abc")

        command()

        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)

        # 验证响应结构
        assert result["success"] is False
        assert "error" in result
        assert "data" not in result
        assert result["error"]["code"] == "INVALID_INPUT"
        assert result["error"]["message"] == "Invalid amount: abc"

    def test_complete_success_workflow(self, capsys):
        """测试完整的成功处理工作流"""
        @json_output
        def command():
            return {"accounts": [{"id": 1, "name": "Cash"}, {"id": 2, "name": "Bank"}]}

        command()

        captured = capsys.readouterr()
        import json
        result = json.loads(captured.out)

        # 验证响应结构
        assert result["success"] is True
        assert "data" in result
        assert "error" not in result
        assert len(result["data"]["accounts"]) == 2
