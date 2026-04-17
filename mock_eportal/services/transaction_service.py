"""
transaction_service.py - Transaction data access service (simulating MCP processing)
Updated for CardDemo alignment with accountNumber field.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mock_eportal.utils import load_json_file

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
            self._data = load_json_file(data_file)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all transaction records"""
        return self._data

    def get_by_account_number(self, account_number: str) -> List[Dict[str, Any]]:
        """Filter transactions by account number"""
        return [r for r in self._data if r["accountNumber"] == account_number]

    def get_by_account(self, account_id: str) -> List[Dict[str, Any]]:
        """Deprecated alias retained for compatibility."""
        return self.get_by_account_number(account_id)

    def get_by_date_range(self, start: str, end: str) -> List[Dict[str, Any]]:
        """Filter transactions by date range (YYYY-MM-DD)"""
        return [r for r in self._data if start <= r["transactionDate"] <= end]

    def get_by_type(self, txn_type: str) -> List[Dict[str, Any]]:
        """Filter by transaction type (CREDIT/DEBIT/TRANSFER/PAYMENT)"""
        return [
            r for r in self._data if r["transactionType"].upper() == txn_type.upper()
        ]

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter by transaction status (POSTED/PENDING/DECLINED)"""
        return [
            r
            for r in self._data
            if r["transactionStatus"].upper() == status.upper()
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
