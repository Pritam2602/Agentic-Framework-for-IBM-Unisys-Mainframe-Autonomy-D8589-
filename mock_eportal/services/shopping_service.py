"""Service for Unisys shopping behavior data generated from IBM CardDemo."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from mock_eportal.utils import load_json_file

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "unisys"
DATA_FILE = DATA_DIR / "shopping.json"
WRITABLE_FIELDS = {
    "loyaltyPoints",
    "browsingSessionMinutes",
    "cartStatus",
    "merchantCategory",
}


class ShoppingService:
    """Service layer for customer shopping behavior data."""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load shopping behavior records from JSON."""
        if DATA_FILE.exists():
            self._data = load_json_file(DATA_FILE)

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

    def update_enrichment(
        self,
        customer_id: str,
        date: str,
        merchant: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update writable enrichment fields for one shopping record."""
        safe_updates = {
            key: value
            for key, value in updates.items()
            if key in WRITABLE_FIELDS
        }
        if not safe_updates:
            return None

        for record in self._data:
            if (
                str(record.get("customerId")) == str(customer_id)
                and record.get("date") == date
                and str(record.get("merchant", "")).lower() == merchant.lower()
            ):
                record.update(safe_updates)
                self._persist()
                return record
        return None

    def create_shopping_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shopping enrichment event."""
        required = {"customerId", "merchant", "amount", "date", "category"}
        missing = sorted(required - set(record))
        if missing:
            raise ValueError(f"Missing required field(s): {', '.join(missing)}")

        self._data.append(record)
        self._persist()
        return record

    def _persist(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with DATA_FILE.open("w", encoding="utf-8") as file:
            json.dump(self._data, file, indent=4)
            file.write("\n")
