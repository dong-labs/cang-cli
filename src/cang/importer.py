"""导入器模块

实现 cang-cli 的数据导入功能。
"""

from typing import Any
from dong.io import BaseImporter, ImporterRegistry
from .db.connection import get_cursor


class CangImporter(BaseImporter):
    """仓咚咚导入器"""
    
    name = "cang"
    
    def validate(self, data: dict[str, Any]) -> tuple[bool, str]:
        """
        验证导入数据格式
        
        Args:
            data: 数据字典
            
        Returns:
            (是否有效, 错误信息)
        """
        if not isinstance(data, dict):
            return False, "数据必须是字典格式"
        
        # 检查是否至少有一个数据类型
        valid_keys = [
            "accounts", "transactions", "categories", 
            "transfers", "invest_transactions", "budgets", "assets"
        ]
        if not any(key in data for key in valid_keys):
            return False, "数据中未找到有效的财务数据"
        
        return True, ""
    
    def import_data(
        self, 
        data: dict[str, Any], 
        merge: bool = False
    ) -> dict[str, Any]:
        """
        导入数据
        
        Args:
            data: 数据字典
            merge: 是否合并（True=追加，False=清空后导入）
            
        Returns:
            导入结果统计
        """
        results = {}
        
        # 导入各类数据
        if "accounts" in data:
            results["accounts"] = self._import_accounts(
                data["accounts"], merge
            )
        
        if "categories" in data:
            results["categories"] = self._import_categories(
                data["categories"], merge
            )
        
        if "transactions" in data:
            results["transactions"] = self._import_transactions(
                data["transactions"], merge
            )
        
        if "transfers" in data:
            results["transfers"] = self._import_transfers(
                data["transfers"], merge
            )
        
        if "invest_transactions" in data:
            results["invest_transactions"] = self._import_invest_transactions(
                data["invest_transactions"], merge
            )
        
        if "budgets" in data:
            results["budgets"] = self._import_budgets(
                data["budgets"], merge
            )
        
        if "assets" in data:
            results["assets"] = self._import_assets(
                data["assets"], merge
            )
        
        return results
    
    def _import_accounts(
        self, 
        accounts: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入账户"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM accounts")
            
            imported = 0
            skipped = 0
            
            for acc in accounts:
                if merge:
                    cur.execute(
                        "SELECT id FROM accounts WHERE name = ?",
                        (acc["name"],)
                    )
                    if cur.fetchone():
                        skipped += 1
                        continue
                
                cur.execute(
                    """
                    INSERT INTO accounts (name, type, currency)
                    VALUES (?, ?, ?)
                    """,
                    (acc["name"], acc["type"], acc.get("currency", "CNY"))
                )
                imported += 1
            
            return {"imported": imported, "skipped": skipped}
    
    def _import_categories(
        self, 
        categories: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入分类"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM categories")
            
            imported = 0
            skipped = 0
            
            for cat in categories:
                if merge:
                    cur.execute(
                        "SELECT id FROM categories WHERE name = ?",
                        (cat["name"],)
                    )
                    if cur.fetchone():
                        skipped += 1
                        continue
                
                cur.execute(
                    "INSERT INTO categories (name) VALUES (?)",
                    (cat["name"],)
                )
                imported += 1
            
            return {"imported": imported, "skipped": skipped}
    
    def _import_transactions(
        self, 
        transactions: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入交易记录"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM transactions")
            
            imported = 0
            skipped = 0
            
            for tx in transactions:
                amount_cents = int(tx["amount"] * 100)
                
                if merge:
                    # 检查重复（同日期、同金额、同账户）
                    cur.execute(
                        """
                        SELECT id FROM transactions 
                        WHERE date = ? AND amount_cents = ? AND account_id = ?
                        """,
                        (tx["date"], amount_cents, tx.get("account_id"))
                    )
                    if cur.fetchone():
                        skipped += 1
                        continue
                
                cur.execute(
                    """
                    INSERT INTO transactions 
                    (date, amount_cents, account_id, category, note)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        tx["date"],
                        amount_cents,
                        tx.get("account_id"),
                        tx.get("category"),
                        tx.get("note"),
                    )
                )
                imported += 1
            
            return {"imported": imported, "skipped": skipped}
    
    def _import_transfers(
        self, 
        transfers: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入转账记录"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM transfers")
            
            imported = 0
            
            for tf in transfers:
                cur.execute(
                    """
                    INSERT INTO transfers 
                    (from_account_id, to_account_id, amount_cents, fee_cents, date, note)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tf["from_account_id"],
                        tf["to_account_id"],
                        int(tf["amount"] * 100),
                        int(tf.get("fee", 0) * 100),
                        tf["date"],
                        tf.get("note"),
                    )
                )
                imported += 1
            
            return {"imported": imported, "skipped": 0}
    
    def _import_invest_transactions(
        self, 
        invests: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入投资交易"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM invest_transactions")
            
            imported = 0
            
            for inv in invests:
                cur.execute(
                    """
                    INSERT INTO invest_transactions 
                    (date, symbol, type, price_cents, quantity, amount_cents, fee_cents, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inv["date"],
                        inv["symbol"],
                        inv["type"],
                        int(inv["price"] * 100),
                        inv["quantity"],
                        int(inv["amount"] * 100),
                        int(inv.get("fee", 0) * 100),
                        inv.get("note"),
                    )
                )
                imported += 1
            
            return {"imported": imported, "skipped": 0}
    
    def _import_budgets(
        self, 
        budgets: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入预算"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM budgets")
            
            imported = 0
            
            for bd in budgets:
                cur.execute(
                    """
                    INSERT INTO budgets 
                    (category, amount_cents, period, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        bd["category"],
                        int(bd["amount"] * 100),
                        bd["period"],
                        bd["start_date"],
                        bd["end_date"],
                    )
                )
                imported += 1
            
            return {"imported": imported, "skipped": 0}
    
    def _import_assets(
        self, 
        assets: list[dict], 
        merge: bool
    ) -> dict[str, int]:
        """导入资产"""
        with get_cursor() as cur:
            if not merge:
                cur.execute("DELETE FROM assets")
            
            imported = 0
            skipped = 0
            
            for asset in assets:
                if merge:
                    cur.execute(
                        "SELECT id FROM assets WHERE name = ? AND type = ?",
                        (asset["name"], asset["type"])
                    )
                    if cur.fetchone():
                        skipped += 1
                        continue
                
                cur.execute(
                    """
                    INSERT INTO assets 
                    (name, type, amount_cents, value_cents, currency, code)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset["name"],
                        asset["type"],
                        int(asset["amount"] * 100) if asset.get("amount") else None,
                        int(asset["value"] * 100),
                        asset.get("currency", "CNY"),
                        asset.get("code"),
                    )
                )
                imported += 1
            
            return {"imported": imported, "skipped": skipped}


# 注册到 dong.io
ImporterRegistry.register(CangImporter())
