"""Service for Unisys inventory availability data."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from mock_eportal.utils import load_json_file

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "unisys"
DATA_FILE = DATA_DIR / "inventory.json"


class InventoryService:
    """Service layer for product inventory and availability data."""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load inventory records from JSON."""
        if DATA_FILE.exists():
            self._data = load_json_file(DATA_FILE)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all inventory records."""
        return self._data

    def search(
        self,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
        sku: Optional[str] = None,
        availability_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filter inventory records by merchant, category, SKU, or status."""
        records = self._data
        if merchant:
            records = [
                r for r in records
                if str(r.get("merchant", "")).lower() == merchant.lower()
            ]
        if category:
            records = [
                r for r in records
                if str(r.get("category", "")).lower() == category.lower()
            ]
        if sku:
            records = [
                r for r in records
                if str(r.get("sku", "")).lower() == sku.lower()
            ]
        if availability_status:
            records = [
                r for r in records
                if str(r.get("availabilityStatus", "")).lower() == availability_status.lower()
            ]
        return records

    def get_field_names(self) -> List[str]:
        """Return available field names."""
        if self._data:
            return list(self._data[0].keys())
        return []
