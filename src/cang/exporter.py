"""导出器模块

实现 cang-cli 的数据导出功能。
"""

from typing import Any
from dong.io import BaseExporter, ExporterRegistry
from .db.connection import get_cursor


class CangExporter(BaseExporter):
    """仓咚咚导出器"""
    
    name = "cang"
    
    def fetch_all(self) -> list[dict[str, Any]]:
        """
        获取所有数据（合并所有表）
        
        Returns:
            所有数据
        """
        return {
            "accounts": self._fetch_accounts(),
            "transactions": self._fetch_transactions(),
            "categories": self._fetch_categories(),
            "transfers": self._fetch_transfers(),
            "invest_transactions": self._fetch_invest_transactions(),
            "budgets": self._fetch_budgets(),
            "assets": self._fetch_assets(),
        }
    
    def _fetch_accounts(self) -> list[dict[str, Any]]:
        """获取账户"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT id, name, type, currency, created_at
                FROM accounts
                ORDER BY created_at
            """)
            return [dict(row) for row in cur.fetchall()]
    
    def _fetch_transactions(self) -> list[dict[str, Any]]:
        """获取交易记录"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, date, amount_cents, account_id, 
                    category, note, created_at
                FROM transactions
                ORDER BY date DESC
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "date": row["date"],
                    "amount": row["amount_cents"] / 100,
                    "account_id": row["account_id"],
                    "category": row["category"],
                    "note": row["note"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
    
    def _fetch_categories(self) -> list[dict[str, Any]]:
        """获取分类"""
        with get_cursor() as cur:
            cur.execute("SELECT id, name FROM categories ORDER BY name")
            return [dict(row) for row in cur.fetchall()]
    
    def _fetch_transfers(self) -> list[dict[str, Any]]:
        """获取转账记录"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, from_account_id, to_account_id, 
                    amount_cents, fee_cents, date, note, created_at
                FROM transfers
                ORDER BY date DESC
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "from_account_id": row["from_account_id"],
                    "to_account_id": row["to_account_id"],
                    "amount": row["amount_cents"] / 100,
                    "fee": row["fee_cents"] / 100,
                    "date": row["date"],
                    "note": row["note"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
    
    def _fetch_invest_transactions(self) -> list[dict[str, Any]]:
        """获取投资交易"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, date, symbol, type, price_cents, 
                    quantity, amount_cents, fee_cents, note, created_at
                FROM invest_transactions
                ORDER BY date DESC
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "date": row["date"],
                    "symbol": row["symbol"],
                    "type": row["type"],
                    "price": row["price_cents"] / 100,
                    "quantity": row["quantity"],
                    "amount": row["amount_cents"] / 100,
                    "fee": row["fee_cents"] / 100,
                    "note": row["note"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
    
    def _fetch_budgets(self) -> list[dict[str, Any]]:
        """获取预算"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, category, amount_cents, period, 
                    start_date, end_date, created_at
                FROM budgets
                ORDER BY start_date DESC
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "category": row["category"],
                    "amount": row["amount_cents"] / 100,
                    "period": row["period"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
    
    def _fetch_assets(self) -> list[dict[str, Any]]:
        """获取资产"""
        with get_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, name, type, amount_cents, value_cents,
                    currency, code, created_at
                FROM assets
                ORDER BY created_at
            """)
            rows = cur.fetchall()
            return [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["type"],
                    "amount": row["amount_cents"] / 100 if row["amount_cents"] else None,
                    "value": row["value_cents"] / 100,
                    "currency": row["currency"],
                    "code": row["code"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
    
    def to_markdown(self) -> str:
        """导出为 Markdown 格式"""
        data = self.fetch_all()
        lines = ["# 仓咚咚 - 财务数据导出\n"]
        
        # 账户
        if data["accounts"]:
            lines.append("## 账户\n")
            for acc in data["accounts"]:
                lines.append(f"- {acc['name']} ({acc['type']})")
        
        # 交易记录
        if data["transactions"]:
            lines.append(f"\n## 交易记录 ({len(data['transactions'])} 条)\n")
            for tx in data["transactions"][:20]:
                lines.append(f"- {tx['date']} | {tx['category']} | ¥{tx['amount']:.2f}")
                if tx['note']:
                    lines.append(f"  - {tx['note']}")
        
        # 资产
        if data["assets"]:
            lines.append(f"\n## 资产 ({len(data['assets'])} 项)\n")
            for asset in data["assets"]:
                lines.append(f"- {asset['name']} ({asset['type']}): ¥{asset['value']:.2f}")
        
        return "\n".join(lines)


# 注册到 dong.io
ExporterRegistry.register(CangExporter())
