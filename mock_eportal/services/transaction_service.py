"""
transaction_service.py - Transaction data access service (simulating MCP processing)
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TransactionService:
    """Service layer for transaction data - simulates MCP transaction processing"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load transaction records from JSON"""
        data_file = DATA_DIR / "transaction.json"
        if data_file.exists():
            with open(data_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all transaction records"""
        return self._data

    def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Filter transactions by account ID"""
        return [
            r for r in self._data
            if r["accountId"] == account_id
        ]

    def get_by_date_range(
        self, start: str, end: str
    ) -> List[Dict[str, Any]]:
        """Filter transactions by date range (YYYY-MM-DD)"""
        return [
            r for r in self._data
            if start <= r["transactionDate"] <= end
        ]

    def get_by_type(self, txn_type: str) -> List[Dict[str, Any]]:
        """Filter by transaction type (credit/debit)"""
        return [
            r for r in self._data
            if r["transactionType"].lower() == txn_type.lower()
        ]

    def get_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single transaction by ID"""
        for record in self._data:
            if record["transactionId"] == transaction_id:
                return record
        return None

    def get_field_names(self) -> List[str]:
        """Return available field names"""
        if self._data:
            return list(self._data[0].keys())
        return []
