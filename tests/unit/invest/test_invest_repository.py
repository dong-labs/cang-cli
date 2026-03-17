"""测试 invest.repository 模块"""

import pytest
from cang.invest.repository import (
    list_invest_transactions,
    create_invest_transaction,
    get_invest_transaction_by_id,
    get_holdings,
    get_profit,
)


class TestListInvestTransactions:
    """测试 list_invest_transactions 函数"""

    def test_empty_list(self, patch_db_connection):
        """测试：空交易列表"""
        result = list_invest_transactions()
        assert result == []

    def test_with_transactions(self, patch_db_connection):
        """测试：有交易数据"""
        create_invest_transaction(
            date="2026-03-15",
            symbol="510300",
            tx_type="buy",
            price_cents=40000,
            quantity=100,
            amount_cents=4000000
        )
        
        result = list_invest_transactions()
        assert len(result) == 1


class TestCreateInvestTransaction:
    """测试 create_invest_transaction 函数"""

    def test_create_buy(self, patch_db_connection):
        """测试：创建买入交易"""
        result = create_invest_transaction(
            date="2026-03-15",
            symbol="510300",
            tx_type="buy",
            price_cents=40000,
            quantity=100,
            amount_cents=4000000
        )
        
        assert result["id"] > 0
        assert result["type"] == "buy"


class TestGetHoldings:
    """测试 get_holdings 函数"""

    def test_empty_holdings(self, patch_db_connection):
        """测试：无持仓"""
        result = get_holdings()
        assert result == []

    def test_single_stock_holding(self, patch_db_connection):
        """测试：单个股票持仓"""
        create_invest_transaction(
            date="2026-03-15",
            symbol="510300",
            tx_type="buy",
            price_cents=40000,
            quantity=100,
            amount_cents=4000000
        )
        
        result = get_holdings()
        assert len(result) == 1
        assert result[0]["symbol"] == "510300"


class TestGetProfit:
    """测试 get_profit 函数"""

    def test_no_transactions(self, patch_db_connection):
        """测试：无交易记录"""
        result = get_profit()
        
        assert result["cost_basis_cents"] == 0
        assert result["proceeds_cents"] == 0
        assert result["realized_profit_cents"] == 0
        assert result["dividend_cents"] == 0

    def test_only_buy_no_sell(self, patch_db_connection):
        """测试：只买入未卖出"""
        create_invest_transaction(
            date="2026-03-10",
            symbol="510300",
            tx_type="buy",
            price_cents=40000,
            quantity=100,
            amount_cents=4000000
        )
        
        result = get_profit()
        # 成本 4000 元 + 0 手续费
        assert result["cost_basis_cents"] == 4000000
        # 未卖出，无已实现盈亏
        assert result["realized_profit_cents"] == -4000000

    def test_buy_and_sell_profit(self, patch_db_connection):
        """测试：买入后卖出盈利"""
        create_invest_transaction(
            date="2026-03-10",
            symbol="510300",
            tx_type="buy",
            price_cents=40000,
            quantity=100,
            amount_cents=4000000
        )
        create_invest_transaction(
            date="2026-03-15",
            symbol="510300",
            tx_type="sell",
            price_cents=45000,
            quantity=50,
            amount_cents=2250000
        )
        
        result = get_profit()
        # 买入成本 4000
        assert result["cost_basis_cents"] == 4000000
        # 卖出收入 2250
        assert result["proceeds_cents"] == 2250000

    def test_with_dividend(self, patch_db_connection):
        """测试：包含分红"""
        create_invest_transaction(
            date="2026-03-10",
            symbol="510300",
            tx_type="buy",
            price_cents=40000,
            quantity=100,
            amount_cents=4000000
        )
        create_invest_transaction(
            date="2026-03-15",
            symbol="510300",
            tx_type="dividend",
            price_cents=0,
            quantity=0,
            amount_cents=50000
        )
        
        result = get_profit()
        assert result["dividend_cents"] == 50000
        # 总收益 = 已实现盈亏 + 分红
        # 已实现盈亏 = 卖出收入(0) - 买入成本(4000) = -4000
        # 总收益 = -4000 + 500 = -3500
        assert result["total_profit_cents"] == -3950000
