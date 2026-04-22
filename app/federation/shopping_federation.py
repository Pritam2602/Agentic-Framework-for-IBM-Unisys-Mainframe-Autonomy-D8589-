"""Federation logic for IBM transactions + Unisys shopping behavior."""

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
        category = str(record["category"])
        totals[category] = round(totals.get(category, 0) + float(record["amount"]), 2)
    return totals


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
    unisys_spend = round(sum(float(record["amount"]) for record in unisys_records), 2)

    return {
        "customerId": customer_id,
        "date": date,
        "federation": {
            "ibm_spend": ibm_spend,
            "unisys_spend": unisys_spend,
            "combined_spend": round(ibm_spend + unisys_spend, 2),
        },
        "category_analysis": category_analysis(unisys_records),
        "behavior_insights": behavior_insights(unisys_records),
        "metadata": {
            "sources_used": ["IBM CardDemo", "Unisys ePortal"],
            "join_key": "customerId",
            "mapping": {
                "customerId": "customerId",
                "amount": "transactionAmount",
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
