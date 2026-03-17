"""测试 budget.repository 模块"""

import pytest
from cang.budget.repository import (
    list_budgets,
    get_budget_by_id,
    create_budget,
    update_budget,
    delete_budget,
    get_all_budgets_status,
)


class TestListBudgets:
    """测试 list_budgets 函数"""

    def test_empty_list(self, patch_db_connection):
        """测试：空预算列表"""
        result = list_budgets()
        assert result == []

    def test_with_budgets(self, patch_db_connection):
        """测试：有预算数据"""
        create_budget(
            category="food",
            amount_cents=120000,
            period="monthly",
            start_date="2026-03-01",
            end_date="2026-03-31"
        )
        create_budget(
            category="transport",
            amount_cents=50000,
            period="monthly",
            start_date="2026-03-01",
            end_date="2026-03-31"
        )
        
        result = list_budgets()
        assert len(result) == 2


class TestCreateBudget:
    """测试 create_budget 函数"""

    def test_create_monthly_budget(self, patch_db_connection):
        """测试：创建月度预算"""
        result = create_budget(
            category="food",
            amount_cents=120000,
            period="monthly",
            start_date="2026-03-01",
            end_date="2026-03-31"
        )
        
        assert result["id"] > 0
        assert result["category"] == "food"


class TestGetAllBudgetsStatus:
    """测试 get_all_budgets_status 函数"""

    def test_no_budgets(self, patch_db_connection):
        """测试：无预算"""
        result = get_all_budgets_status()
        assert result == []

    def test_budget_with_no_spending(self, patch_db_connection):
        """测试：有预算但无消费"""
        create_budget(
            category="food",
            amount_cents=120000,
            period="monthly",
            start_date="2026-03-01",
            end_date="2026-03-31"
        )
        
        result = get_all_budgets_status()
        assert len(result) == 1
        assert result[0]["category"] == "food"
        assert result[0]["budget"] == 120000
        assert result[0]["spent"] == 0
