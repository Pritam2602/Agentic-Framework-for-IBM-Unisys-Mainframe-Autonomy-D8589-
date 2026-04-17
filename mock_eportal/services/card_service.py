"""
card_service.py - Card data access service (simulating VSAM backend)

Represents credit/debit cards from AWS CardDemo.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mock_eportal.utils import load_json_file

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class CardService:
    """Service layer for card data - simulates VSAM file access"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load card records from JSON (simulates VSAM READ)"""
        data_file = DATA_DIR / "card.json"
        if data_file.exists():
            self._data = load_json_file(data_file)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all card records"""
        return self._data

    def get_by_card_number(self, card_number: str) -> Optional[Dict[str, Any]]:
        """Fetch card by card number (simulates VSAM keyed READ)"""
        for record in self._data:
            if record["cardNumber"] == card_number:
                return record
        return None

    def get_by_customer_id(self, customer_id: str) -> List[Dict[str, Any]]:
        """Fetch cards by customer ID (1:1 relationship in CardDemo)"""
        return [r for r in self._data if r["customerId"] == customer_id]

    def get_by_account_number(self, account_number: str) -> Optional[Dict[str, Any]]:
        """Fetch card by account number (1:1 relationship in CardDemo)"""
        for record in self._data:
            if record["accountNumber"] == account_number:
                return record
        return None

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter cards by status"""
        return [r for r in self._data if r["cardStatus"].upper() == status.upper()]

    def get_by_type(self, card_type: str) -> List[Dict[str, Any]]:
        """Filter cards by type (CREDIT/DEBIT)"""
        return [r for r in self._data if r["cardType"].upper() == card_type.upper()]

    def get_by_cardholder_name(self, name: str) -> List[Dict[str, Any]]:
        """Filter cards by cardholder name"""
        return [r for r in self._data if name.lower() in r["cardholderName"].lower()]

    def get_field_names(self) -> List[str]:
        """Return available field names"""
        if self._data:
            return list(self._data[0].keys())
        return []
