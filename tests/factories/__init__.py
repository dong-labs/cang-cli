"""测试数据工厂模块

提供用于创建测试数据的工厂函数。
"""

from cang.db.utils import to_cents


class AccountFactory:
    """账户数据工厂"""

    @staticmethod
    def cash(name: str = "现金", currency: str = "CNY") -> dict:
        """创建现金账户"""
        return {
            "name": name,
            "type": "cash",
            "currency": currency,
        }

    @staticmethod
    def bank(name: str = "招商银行", currency: str = "CNY") -> dict:
        """创建银行账户"""
        return {
            "name": name,
            "type": "bank",
            "currency": currency,
        }

    @staticmethod
    def digital(name: str = "微信", currency: str = "CNY") -> dict:
        """创建数字钱包账户"""
        return {
            "name": name,
            "type": "digital",
            "currency": currency,
        }


class TransactionFactory:
    """交易数据工厂"""

    @staticmethod
    def expense(
        amount: float | str,
        account_id: int = 1,
        category: str = "餐饮",
        note: str = "午餐",
        date: str = "2026-03-15"
    ) -> dict:
        """创建支出交易"""
        return {
            "date": date,
            "amount_cents": to_cents(amount),
            "account_id": account_id,
            "category": category,
            "note": note,
        }

    @staticmethod
    def income(
        amount: float | str,
        account_id: int = 1,
        category: str = "工资",
        note: str = "月薪",
        date: str = "2026-03-15"
    ) -> dict:
        """创建收入交易"""
        return {
            "date": date,
            "amount_cents": to_cents(amount),
            "account_id": account_id,
            "category": category,
            "note": note,
        }


class AssetFactory:
    """资产数据工厂"""

    @staticmethod
    def cash(value: float | str = 1000) -> dict:
        """创建现金资产"""
        return {
            "name": "现金",
            "type": "cash",
            "amount_cents": to_cents(value),
            "value_cents": to_cents(value),
            "currency": "CNY",
            "code": None,
        }

    @staticmethod
    def stock(
        name: str = "腾讯控股",
        code: str = "00700",
        quantity: int = 100,
        price: float = 300.0
    ) -> dict:
        """创建股票资产"""
        value_cents = to_cents(quantity * price)
        return {
            "name": name,
            "type": "stock",
            "amount_cents": quantity,
            "value_cents": value_cents,
            "currency": "HKD",
            "code": code,
        }

    @staticmethod
    def fund(
        name: str = "沪深300ETF",
        code: str = "510300",
        quantity: int = 1000,
        price: float = 4.0
    ) -> dict:
        """创建基金资产"""
        value_cents = to_cents(quantity * price)
        return {
            "name": name,
            "type": "fund",
            "amount_cents": quantity,
            "value_cents": value_cents,
            "currency": "CNY",
            "code": code,
        }

    @staticmethod
    def real_estate(
        name: str = "房产",
        value: float = 3500000
    ) -> dict:
        """创建房产资产"""
        return {
            "name": name,
            "type": "real_estate",
            "amount_cents": 1,
            "value_cents": to_cents(value),
            "currency": "CNY",
            "code": None,
        }


class BudgetFactory:
    """预算数据工厂"""

    @staticmethod
    def monthly(
        category: str = "餐饮",
        amount: float = 1200,
        month: int = 3,
        year: int = 2026
    ) -> dict:
        """创建月度预算"""
        import calendar
        from datetime import datetime

        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"

        return {
            "category": category,
            "amount_cents": to_cents(amount),
            "period": "monthly",
            "start_date": start_date,
            "end_date": end_date,
        }
