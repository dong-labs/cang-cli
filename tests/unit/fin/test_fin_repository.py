"""测试 fin.repository 模块

测试财务流动数据访问层的所有函数。
"""

import pytest
from cang.fin.repository import (
    # Account 相关
    list_accounts,
    get_account_by_id,
    get_account_by_name,
    create_account,
    # Transaction 相关
    list_transactions,
    get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_account_balance,
    # Category 相关
    list_categories,
    get_category_by_id,
    get_category_by_name,
    create_category,
    # Transfer 相关
    create_transfer,
    get_transfer_by_id,
    list_transfers,
    # Summary 相关
    get_transaction_summary,
)


# =============================================================================
# Account 相关测试
# =============================================================================

class TestListAccounts:
    """测试 list_accounts 函数"""
    
    def test_empty_list(self, patch_db_connection):
        """测试：空账户列表"""
        result = list_accounts()
        assert result == []
    
    def test_with_single_account(self, patch_db_connection):
        """测试：单个账户"""
        # 先创建一个账户
        create_account("现金", "cash")
        
        result = list_accounts()
        assert len(result) == 1
        assert result[0]["name"] == "现金"
        assert result[0]["type"] == "cash"
    
    def test_with_multiple_accounts(self, patch_db_connection):
        """测试：多个账户"""
        create_account("现金", "cash")
        create_account("招商银行", "bank")
        create_account("微信", "digital")
        
        result = list_accounts()
        assert len(result) == 3
        # 按_id 排序返回
        assert result[0]["name"] == "现金"
        assert result[1]["name"] == "招商银行"


class TestGetAccountById:
    """测试 get_account_by_id 函数"""
    
    def test_existing_account(self, patch_db_connection):
        """测试：存在的账户"""
        account = create_account("测试账户", "cash")
        
        result = get_account_by_id(account["id"])
        assert result is not None
        assert result["id"] == account["id"]
        assert result["name"] == "测试账户"
    
    def test_non_existing_account(self, patch_db_connection):
        """测试：不存在的账户"""
        result = get_account_by_id(99999)
        assert result is None


class TestGetAccountByName:
    """测试 get_account_by_name 函数"""
    
    def test_existing_account(self, patch_db_connection):
        """测试：存在的账户名"""
        create_account("招商银行", "bank")
        
        result = get_account_by_name("招商银行")
        assert result is not None
        assert result["name"] == "招商银行"
    
    def test_non_existing_account(self, patch_db_connection):
        """测试：不存在的账户名"""
        result = get_account_by_name("不存在的账户")
        assert result is None


class TestCreateAccount:
    """测试 create_account 函数"""
    
    def test_create_cash_account(self, patch_db_connection):
        """测试：创建现金账户"""
        result = create_account("现金", "cash", "CNY")
        
        assert result["name"] == "现金"
        assert result["type"] == "cash"
        assert result["currency"] == "CNY"
        assert result["id"] > 0
    
    def test_create_with_default_currency(self, patch_db_connection):
        """测试：使用默认货币 CNY"""
        result = create_account("测试", "bank")
        
        assert result["currency"] == "CNY"
    
    def test_create_with_different_currency(self, patch_db_connection):
        """测试：创建不同货币账户"""
        result = create_account("HK Bank", "bank", "HKD")
        
        assert result["currency"] == "HKD"


# =============================================================================
# Transaction 相关测试
# =============================================================================

class TestListTransactions:
    """测试 list_transactions 函数"""
    
    def test_empty_list(self, patch_db_connection, account_factory):
        """测试：空交易列表"""
        result = list_transactions()
        assert result == []
    
    def test_with_transactions(self, patch_db_connection, account_factory):
        """测试：有交易数据"""
        account = account_factory(name="测试账户")
        create_transaction("2026-03-15", -2990, account["id"], "餐饮", "午餐")
        create_transaction("2026-03-14", -5000, account["id"], "交通", "加油")
        
        result = list_transactions()
        assert len(result) == 2
        # 按日期降序、id 降序
        assert result[0]["date"] == "2026-03-15"
    
    def test_with_limit(self, patch_db_connection, account_factory):
        """测试：限制返回数量"""
        account = account_factory(name="测试账户")
        for i in range(5):
            create_transaction(f"2026-03-{15-i:02d}", -1000, account["id"])
        
        result = list_transactions(limit=3)
        assert len(result) == 3
    
    def test_filter_by_account(self, patch_db_connection, account_factory):
        """测试：按账户筛选"""
        account1 = account_factory(name="账户1")
        account2 = account_factory(name="账户2")
        create_transaction("2026-03-15", -1000, account1["id"])
        create_transaction("2026-03-15", -2000, account2["id"])
        
        result = list_transactions(account_id=account1["id"])
        assert len(result) == 1
        assert result[0]["account_id"] == account1["id"]
    
    def test_filter_by_category(self, patch_db_connection, account_factory):
        """测试：按分类筛选"""
        account = account_factory(name="测试账户")
        create_transaction("2026-03-15", -1000, account["id"], "餐饮")
        create_transaction("2026-03-14", -2000, account["id"], "交通")
        
        result = list_transactions(category="餐饮")
        assert len(result) == 1
        assert result[0]["category"] == "餐饮"


class TestGetTransactionById:
    """测试 get_transaction_by_id 函数"""
    
    def test_existing_transaction(self, patch_db_connection, account_factory):
        """测试：存在的交易"""
        account = account_factory(name="测试账户")
        tx = create_transaction("2026-03-15", -2990, account["id"], "餐饮")
        
        result = get_transaction_by_id(tx["id"])
        assert result is not None
        assert result["id"] == tx["id"]
    
    def test_non_existing_transaction(self, patch_db_connection):
        """测试：不存在的交易"""
        result = get_transaction_by_id(99999)
        assert result is None


class TestCreateTransaction:
    """测试 create_transaction 函数"""
    
    def test_create_expense(self, patch_db_connection, account_factory):
        """测试：创建支出交易"""
        account = account_factory(name="测试账户")
        
        result = create_transaction(
            date="2026-03-15",
            amount_cents=-2990,
            account_id=account["id"],
            category="餐饮",
            note="午餐"
        )
        
        assert result["id"] > 0
        assert result["amount_cents"] == -2990
        assert result["category"] == "餐饮"
    
    def test_create_without_category(self, patch_db_connection, account_factory):
        """测试：不指定分类"""
        account = account_factory(name="测试账户")
        
        result = create_transaction(
            date="2026-03-15",
            amount_cents=-1000,
            account_id=account["id"]
        )
        
        assert result["id"] > 0
        assert result["category"] is None


class TestUpdateTransaction:
    """测试 update_transaction 函数"""
    
    def test_update_amount(self, patch_db_connection, account_factory):
        """测试：更新金额"""
        account = account_factory(name="测试账户")
        tx = create_transaction("2026-03-15", -1000, account["id"])
        
        result = update_transaction(tx["id"], amount_cents=-2000)
        
        assert result["amount_cents"] == -2000
        # 其他字段不变
        assert result["date"] == "2026-03-15"
    
    def test_update_multiple_fields(self, patch_db_connection, account_factory):
        """测试：更新多个字段"""
        account = account_factory(name="测试账户")
        tx = create_transaction("2026-03-15", -1000, account["id"], "餐饮", "午餐")
        
        result = update_transaction(
            tx["id"],
            amount_cents=-1500,
            category="交通",
            note="打车"
        )
        
        assert result["amount_cents"] == -1500
        assert result["category"] == "交通"
        assert result["note"] == "打车"
    
    def test_update_no_changes(self, patch_db_connection, account_factory):
        """测试：不更新任何字段"""
        account = account_factory(name="测试账户")
        tx = create_transaction("2026-03-15", -1000, account["id"])
        
        result = update_transaction(tx["id"])
        
        assert result["id"] == tx["id"]
        assert result["amount_cents"] == -1000
    
    def test_update_non_existing_transaction(self, patch_db_connection):
        """测试：更新不存在的交易"""
        result = update_transaction(99999, amount_cents=-1000)
        assert result is None


class TestDeleteTransaction:
    """测试 delete_transaction 函数"""
    
    def test_delete_existing(self, patch_db_connection, account_factory):
        """测试：删除存在的交易"""
        account = account_factory(name="测试账户")
        tx = create_transaction("2026-03-15", -1000, account["id"])
        
        result = delete_transaction(tx["id"])
        
        assert result is True
        # 确认已删除
        assert get_transaction_by_id(tx["id"]) is None
    
    def test_delete_non_existing(self, patch_db_connection):
        """测试：删除不存在的交易"""
        result = delete_transaction(99999)
        assert result is False


class TestGetAccountBalance:
    """测试 get_account_balance 函数"""
    
    def test_zero_balance(self, patch_db_connection, account_factory):
        """测试：零余额"""
        account = account_factory(name="测试账户")
        
        balance = get_account_balance(account["id"])
        assert balance == 0
    
    def test_with_transactions(self, patch_db_connection, account_factory):
        """测试：有交易记录"""
        account = account_factory(name="测试账户")
        create_transaction("2026-03-15", -2990, account["id"])  # 支出
        create_transaction("2026-03-14", 5000, account["id"])   # 收入
        
        balance = get_account_balance(account["id"])
        assert balance == 2010  # 5000 - 2990
    
    def test_multiple_accounts(self, patch_db_connection, account_factory):
        """测试：多账户独立计算"""
        account1 = account_factory(name="账户1")
        account2 = account_factory(name="账户2")
        
        create_transaction("2026-03-15", -1000, account1["id"])
        create_transaction("2026-03-15", -2000, account2["id"])
        
        assert get_account_balance(account1["id"]) == -1000
        assert get_account_balance(account2["id"]) == -2000


# =============================================================================
# Category 相关测试
# =============================================================================

class TestListCategories:
    """测试 list_categories 函数"""
    
    def test_empty_list(self, patch_db_connection):
        """测试：空分类列表"""
        result = list_categories()
        assert result == []
    
    def test_with_categories(self, patch_db_connection):
        """测试：有分类数据"""
        create_category("餐饮")
        create_category("交通")
        
        result = list_categories()
        assert len(result) == 2
        assert result[0]["name"] == "餐饮"


class TestCreateCategory:
    """测试 create_category 函数"""
    
    def test_create_single(self, patch_db_connection):
        """测试：创建单个分类"""
        result = create_category("餐饮")
        
        assert result["id"] > 0
        assert result["name"] == "餐饮"


# =============================================================================
# Transfer 相关测试
# =============================================================================

class TestCreateTransfer:
    """测试 create_transfer 函数"""
    
    def test_create_transfer(self, patch_db_connection, account_factory):
        """测试：创建转账"""
        from_account = account_factory(name="账户A")
        to_account = account_factory(name="账户B")
        
        result = create_transfer(
            from_account_id=from_account["id"],
            to_account_id=to_account["id"],
            amount_cents=10000,
            date="2026-03-15"
        )
        
        assert result["id"] > 0
        assert result["from_account_id"] == from_account["id"]
        assert result["to_account_id"] == to_account["id"]
        assert result["amount_cents"] == 10000
    
    def test_create_with_fee(self, patch_db_connection, account_factory):
        """测试：带手续费的转账"""
        from_account = account_factory(name="账户A")
        to_account = account_factory(name="账户B")
        
        result = create_transfer(
            from_account_id=from_account["id"],
            to_account_id=to_account["id"],
            amount_cents=10000,
            fee_cents=50,
            date="2026-03-15"
        )
        
        assert result["amount_cents"] == 10000
        assert result["fee_cents"] == 50


# =============================================================================
# Summary 相关测试
# =============================================================================

class TestGetTransactionSummary:
    """测试 get_transaction_summary 函数"""
    
    def test_empty_summary(self, patch_db_connection, account_factory):
        """测试：空数据汇总"""
        account = account_factory(name="测试账户")
        
        result = get_transaction_summary()
        assert result == []
    
    def test_group_by_category(self, patch_db_connection, account_factory):
        """测试：按分类汇总"""
        account = account_factory(name="测试账户")
        create_transaction("2026-03-15", -3000, account["id"], "餐饮")
        create_transaction("2026-03-14", -2000, account["id"], "餐饮")
        create_transaction("2026-03-13", -5000, account["id"], "交通")
        
        result = get_transaction_summary(group_by="category")
        
        assert len(result) == 2
        # 按总金额降序
        assert result[0]["category"] == "餐饮"
        assert result[0]["total"] == -5000
        assert result[1]["category"] == "交通"
    
    def test_with_date_range(self, patch_db_connection, account_factory):
        """测试：日期范围筛选"""
        account = account_factory(name="测试账户")
        create_transaction("2026-03-01", -1000, account["id"], "餐饮")
        create_transaction("2026-03-15", -2000, account["id"], "餐饮")
        create_transaction("2026-03-20", -3000, account["id"], "餐饮")
        
        result = get_transaction_summary(
            start_date="2026-03-10",
            end_date="2026-03-16",
            group_by="category"
        )
        
        assert len(result) == 1
        assert result[0]["total"] == -2000
