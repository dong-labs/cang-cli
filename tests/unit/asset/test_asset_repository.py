"""测试 asset.repository 模块

测试资产数据访问层的所有函数。
"""

import pytest
from cang.asset.repository import (
    list_assets,
    get_asset_by_id,
    create_asset,
    update_asset,
    delete_asset,
    calculate_networth,
    get_asset_schema,
    ASSET_TYPES,
    _build_asset_update_sql,
    _UPDATABLE_ASSET_FIELDS,
)


# =============================================================================
# _build_asset_update_sql() 测试（纯函数，无需 fixture）
# =============================================================================

class TestBuildAssetUpdateSql:
    """测试 _build_asset_update_sql 函数"""

    def test_valid_single_field(self):
        """测试单个有效字段"""
        result = _build_asset_update_sql({"amount_cents"})
        assert result == "amount_cents = ?"

    def test_valid_multiple_fields(self):
        """测试多个有效字段"""
        result = _build_asset_update_sql({"amount_cents", "value_cents"})
        assert result in (
            "amount_cents = ?, value_cents = ?",
            "value_cents = ?, amount_cents = ?",
        )

    def test_invalid_field_raises_error(self):
        """测试无效字段抛出 ValueError"""
        with pytest.raises(ValueError, match="Invalid asset fields"):
            _build_asset_update_sql({"invalid_field"})


# =============================================================================
# list_assets() 测试
# =============================================================================

class TestListAssets:
    """测试 list_assets 函数"""

    def test_empty_list(self, patch_db_connection):
        """测试：空资产列表"""
        result = list_assets()
        assert result == []

    def test_with_assets(self, patch_db_connection):
        """测试：有资产数据"""
        create_asset("现金", "cash", 10000)
        create_asset("招商银行", "bank", 50000)
        
        result = list_assets()
        assert len(result) == 2
        assert result[0]["name"] == "现金"


class TestGetAssetById:
    """测试 get_asset_by_id 函数"""

    def test_existing_asset(self, patch_db_connection):
        """测试：存在的资产"""
        asset = create_asset("测试资产", "cash", 10000)
        
        result = get_asset_by_id(asset["id"])
        assert result is not None
        assert result["name"] == "测试资产"


class TestCreateAsset:
    """测试 create_asset 函数"""

    def test_create_cash(self, patch_db_connection):
        """测试：创建现金资产"""
        result = create_asset("现金", "cash", 10000)
        
        assert result["id"] > 0
        assert result["name"] == "现金"


class TestUpdateAsset:
    """测试 update_asset 函数"""

    def test_update_amount(self, patch_db_connection):
        """测试：更新持有数量"""
        asset = create_asset("测试", "cash", 1000)
        
        result = update_asset(asset["id"], amount=2000)
        
        assert result["amount_cents"] == 2000

    def test_update_value(self, patch_db_connection):
        """测试：更新市值"""
        asset = create_asset("测试", "stock", 100)
        
        result = update_asset(asset["id"], value=50000)
        
        assert result["value_cents"] == 50000

    def test_update_both(self, patch_db_connection):
        """测试：同时更新数量和市值"""
        asset = create_asset("测试", "stock", 100)
        
        result = update_asset(asset["id"], amount=200, value=50000)
        
        assert result["amount_cents"] == 200
        assert result["value_cents"] == 50000


class TestCalculateNetworth:
    """测试 calculate_networth 函数"""

    def test_empty_assets(self, patch_db_connection):
        """测试：没有资产时净资产为 0"""
        result = calculate_networth()
        
        assert result["networth_cents"] == 0
        assert result["asset_count"] == 0

    def test_single_currency(self, patch_db_connection):
        """测试：单一货币净资产"""
        # 注意：创建资产时 value_cents 默认为 0，需要更新
        asset1 = create_asset("现金", "cash", 10000)
        asset2 = create_asset("银行", "bank", 50000)
        update_asset(asset1["id"], value=10000)
        update_asset(asset2["id"], value=50000)
        
        result = calculate_networth()
        
        assert result["networth_cents"] == 60000
        assert result["asset_count"] == 2


class TestAssetTypesConstant:
    """测试 ASSET_TYPES 常量"""

    def test_is_list(self):
        """测试：是列表类型"""
        assert isinstance(ASSET_TYPES, list)

    def test_contains_expected_types(self):
        """测试：包含预期的资产类型"""
        expected = {"cash", "bank", "stock", "fund", "bond", "crypto", 
                    "real_estate", "vehicle", "gold", "other"}
        assert set(ASSET_TYPES) == expected
