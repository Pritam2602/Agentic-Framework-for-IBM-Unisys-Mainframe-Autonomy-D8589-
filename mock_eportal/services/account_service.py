"""
account_service.py - Account data access service (simulating VSAM backend)

Represents financial accounts from AWS CardDemo.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mock_eportal.utils import load_json_file

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class AccountService:
    """Service layer for account data - simulates VSAM file access"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load account records from JSON (simulates VSAM READ)"""
        data_file = DATA_DIR / "account.json"
        if data_file.exists():
            self._data = load_json_file(data_file)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all account records"""
        return self._data

    def get_by_account_number(self, account_number: str) -> Optional[Dict[str, Any]]:
        """Fetch account by account number (simulates VSAM keyed READ)"""
        for record in self._data:
            if record["accountNumber"] == account_number:
                return record
        return None

    def get_by_customer_id(self, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch accounts by customer ID (1:1 relationship in CardDemo)"""
        return [r for r in self._data if r["customerId"] == customer_id]

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter accounts by status"""
        return [r for r in self._data if r["accountStatus"].upper() == status.upper()]

    def get_by_type(self, account_type: str) -> List[Dict[str, Any]]:
        """Filter accounts by type (CREDIT/SAVINGS/CHECKING)"""
        return [r for r in self._data if r["accountType"].upper() == account_type.upper()]

    def get_by_balance_range(
        self, min_balance: float, max_balance: float
    ) -> List[Dict[str, Any]]:
        """Filter accounts by balance range"""
        return [
            r
            for r in self._data
            if min_balance <= r["accountBalance"] <= max_balance
        ]

    def get_field_names(self) -> List[str]:
        """Return available field names"""
        if self._data:
            return list(self._data[0].keys())
        return []
