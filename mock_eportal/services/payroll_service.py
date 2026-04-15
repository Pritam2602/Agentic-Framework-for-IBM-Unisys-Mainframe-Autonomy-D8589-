"""
payroll_service.py - Payroll data access service (simulating COBOL backend)
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class PayrollService:
    """Service layer for payroll data - simulates COBOL PERFORM READ logic"""

    def __init__(self):
        self._data: List[Dict[str, Any]] = []
        self._load_data()

    def _load_data(self):
        """Load payroll records from JSON (simulates COBOL file READ)"""
        data_file = DATA_DIR / "payroll.json"
        if data_file.exists():
            with open(data_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all payroll records"""
        return self._data

    def get_by_employee_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Fetch payroll record by employee ID (simulates COBOL indexed READ)"""
        for record in self._data:
            if record["employeeId"] == employee_id:
                return record
        return None

    def get_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Filter payroll records by department"""
        return [
            r for r in self._data
            if r["department"].lower() == department.lower()
        ]

    def get_by_date_range(
        self, start: str, end: str
    ) -> List[Dict[str, Any]]:
        """
        Filter payroll records by pay period date range.
        Expects start/end in YYYY-MM-DD format; matches against payPeriod (YYYY-MM).
        """
        # Convert YYYY-MM-DD to YYYY-MM for comparison
        start_period = start[:7]  # "2026-03-01" -> "2026-03"
        end_period = end[:7]

        return [
            r for r in self._data
            if start_period <= r["payPeriod"] <= end_period
        ]

    def get_field_names(self) -> List[str]:
        """Return available field names"""
        if self._data:
            return list(self._data[0].keys())
        return []
