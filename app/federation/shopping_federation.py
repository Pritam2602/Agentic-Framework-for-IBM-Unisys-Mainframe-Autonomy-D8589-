"""Federation logic for IBM transactions + Unisys shopping behavior.

IMPORTANT:
    IBM CardDemo transactions already include ALL financial amounts,
    including shopping spend.  Unisys ePortal provides *behavioral
    enrichment* (merchant, category, loyalty, browsing patterns) — its
    amount field mirrors IBM's and must NOT be added on top.

    total_spend = IBM spend only.
    Unisys contributes enrichment (category breakdown, merchant insights,
    loyalty, browsing behavior, cart status).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[2]
IBM_TRANSACTIONS = ROOT / "data" / "ibm" / "transactions.json"
UNISYS_SHOPPING = ROOT / "data" / "unisys" / "shopping.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def transaction_amount(record: dict[str, Any]) -> float:
    return float(record.get("transactionAmount", record.get("amount", 0)))


def transaction_date(record: dict[str, Any]) -> str:
    return str(record.get("transactionDate", record.get("date")))


def filter_ibm_transactions(
    records: list[dict[str, Any]],
    customer_id: int,
    date: Optional[str],
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if int(record["customerId"]) == customer_id
        and (date is None or transaction_date(record) == date)
    ]


def filter_unisys_shopping(
    records: list[dict[str, Any]],
    customer_id: int,
    date: Optional[str],
) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if int(record["customerId"]) == customer_id
        and (date is None or record["date"] == date)
    ]


def category_analysis(records: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for record in records:
        category = str(record.get("category", "unknown"))
        totals[category] = round(totals.get(category, 0) + float(record["amount"]), 2)
    return totals


def loyalty_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise loyalty points from Unisys behavioral data."""
    total_points = sum(int(r.get("loyaltyPoints", 0)) for r in records)
    return {
        "total_loyalty_points": total_points,
        "avg_loyalty_points": round(total_points / len(records), 1) if records else 0,
    }


def cart_analysis(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyse cart statuses from Unisys behavioral data."""
    statuses: dict[str, int] = {}
    for record in records:
        status = str(record.get("cartStatus", "unknown"))
        statuses[status] = statuses.get(status, 0) + 1

    total = len(records) or 1
    return {
        "cart_status_breakdown": statuses,
        "completion_rate": round(statuses.get("completed", 0) / total * 100, 1),
        "abandonment_rate": round(statuses.get("abandoned", 0) / total * 100, 1),
    }


def browsing_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarise browsing session data from Unisys behavioral data."""
    minutes = [int(r.get("browsingSessionMinutes", 0)) for r in records]
    return {
        "total_browsing_minutes": sum(minutes),
        "avg_browsing_minutes": round(sum(minutes) / len(minutes), 1) if minutes else 0,
        "max_browsing_minutes": max(minutes) if minutes else 0,
    }


def behavior_insights(records: list[dict[str, Any]]) -> dict[str, Any]:
    merchant_totals: dict[str, float] = {}
    for record in records:
        merchant = str(record["merchant"])
        merchant_totals[merchant] = round(
            merchant_totals.get(merchant, 0) + float(record["amount"]),
            2,
        )

    categories = category_analysis(records)
    return {
        "top_category": max(categories, key=categories.get) if categories else None,
        "top_merchant": max(merchant_totals, key=merchant_totals.get)
        if merchant_totals
        else None,
        "shopping_events": len(records),
    }


def federate_customer_spend(
    customer_id: int,
    date: Optional[str] = None,
) -> dict[str, Any]:
    """Federate spend data across IBM and Unisys.

    total_spend = IBM spend ONLY.
    Unisys provides behavioral enrichment (categories, merchants, loyalty,
    browsing, cart status) but its amounts are NOT additive.
    """
    ibm_records = filter_ibm_transactions(
        load_json(IBM_TRANSACTIONS),
        customer_id,
        date,
    )
    unisys_records = filter_unisys_shopping(
        load_json(UNISYS_SHOPPING),
        customer_id,
        date,
    )

    ibm_spend = round(sum(transaction_amount(record) for record in ibm_records), 2)

    return {
        "customerId": customer_id,
        "date": date,
        "federation": {
            "total_spend": ibm_spend,
            "ibm_transaction_count": len(ibm_records),
            "unisys_enrichment_count": len(unisys_records),
            "note": (
                "total_spend comes from IBM CardDemo only. "
                "Unisys amounts mirror IBM — they are NOT added."
            ),
        },
        "behavioral_enrichment": {
            "category_analysis": category_analysis(unisys_records),
            "behavior_insights": behavior_insights(unisys_records),
            "loyalty": loyalty_summary(unisys_records),
            "browsing": browsing_summary(unisys_records),
            "cart": cart_analysis(unisys_records),
        },
        "metadata": {
            "sources_used": ["IBM CardDemo", "Unisys ePortal"],
            "join_key": "customerId",
            "mapping": {
                "customerId": "customerId",
                "amount": "transactionAmount (mirror, not additive)",
                "date": "transactionDate",
            },
        },
        "data_sources": {
            "ibm_records": ibm_records,
            "unisys_records": unisys_records,
        },
    }


if __name__ == "__main__":
    result = federate_customer_spend(customer_id=101, date="2026-03-10")
    print(json.dumps(result, indent=4))
