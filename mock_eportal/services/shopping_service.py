"""Service for Unisys shopping behavior data generated from IBM CardDemo."""

from pathlib import Path
from typing import Any, Dict, List

from mock_eportal.utils import load_json_file

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "unisys"


class ShoppingService:
    """Service layer for customer shopping behavior data."""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load shopping behavior records from JSON."""
        data_file = DATA_DIR / "shopping.json"
        if data_file.exists():
            self._data = load_json_file(data_file)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all shopping behavior records."""
        return self._data

    def get_by_customer_id(self, customer_id: str) -> List[Dict[str, Any]]:
        """Filter shopping records by customer ID."""
        return [r for r in self._data if str(r["customerId"]) == str(customer_id)]

    def get_by_date(self, date: str) -> List[Dict[str, Any]]:
        """Filter shopping records by purchase date (YYYY-MM-DD)."""
        return [r for r in self._data if r["date"] == date]

    def get_by_customer_id_and_date(
        self, customer_id: str, date: str
    ) -> List[Dict[str, Any]]:
        """Filter shopping records by customer ID and purchase date."""
        return [
            r
            for r in self._data
            if str(r["customerId"]) == str(customer_id) and r["date"] == date
        ]

    def get_field_names(self) -> List[str]:
        """Return available field names."""
        if self._data:
            return list(self._data[0].keys())
        return []
