"""
Helpers for reading JSON assets used by the mock ePortal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_file(path: Path) -> Any:
    """Load JSON while tolerating UTF-8 BOM-encoded files."""
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)
