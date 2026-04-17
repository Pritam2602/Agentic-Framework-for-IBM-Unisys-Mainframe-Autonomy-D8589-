"""
customer_service.py - Customer data access service (simulating DMSII backend)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mock_eportal.utils import load_json_file

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class CustomerService:
    """Service layer for customer data - simulates DMSII database access"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load customer records from JSON (simulates DMSII FIND)"""
        data_file = DATA_DIR / "customer.json"
        if data_file.exists():
            self._data = load_json_file(data_file)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all customer records"""
        return self._data

    def get_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Fetch customer by ID (simulates DMSII keyed FIND)"""
        for record in self._data:
            if record["customerId"] == customer_id:
                return record
        return None

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Filter customers by status"""
        return [r for r in self._data if r["status"].lower() == status.lower()]

    def get_by_type(self, customer_type: str) -> List[Dict[str, Any]]:
        """Filter customers by type (individual/corporate)"""
        return [
            r
            for r in self._data
            if r["customerType"].lower() == customer_type.lower()
        ]

    def get_field_names(self) -> List[str]:
        """Return available field names"""
        if self._data:
            return list(self._data[0].keys())
        return []
