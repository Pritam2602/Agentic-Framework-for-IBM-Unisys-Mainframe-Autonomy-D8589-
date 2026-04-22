"""
Generate Unisys shopping behavior data from IBM CardDemo transactions.

Input:
  data/ibm/customers.json
  data/ibm/transactions.json

Output:
  data/unisys/shopping.json

The generator is deterministic: no random choices are used. Every Unisys
shopping record is derived from an IBM transaction customerId, date, and amount.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
IBM_DIR = ROOT / "data" / "ibm"
UNISYS_DIR = ROOT / "data" / "unisys"
OUTPUT_FILE = UNISYS_DIR / "shopping.json"

MERCHANTS = ["Amazon", "Flipkart", "Swiggy", "Zomato", "Uber"]
CATEGORIES = ["electronics", "food", "travel", "shopping"]
AMOUNT_FACTORS = [0.60, 0.40, 0.50, 0.25, 0.30, 0.70, 0.45]
DATE_OFFSETS = [0, 1, 2, 0, -1, 1, -2]
MIN_ENTRIES_PER_CUSTOMER = 5
MAX_ENTRIES_PER_CUSTOMER = 15


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
        file.write("\n")


def parse_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def normalize_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    amount = transaction.get("amount", transaction.get("transactionAmount"))
    date = transaction.get("date", transaction.get("transactionDate"))
    if amount is None or date is None:
        raise ValueError(f"Transaction missing amount/date fields: {transaction}")

    return {
        "customerId": int(transaction["customerId"]),
        "amount": float(amount),
        "date": str(date),
    }


def generate_entries(
    customer_id: int,
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not transactions:
        return []

    target_count = min(
        MAX_ENTRIES_PER_CUSTOMER,
        max(MIN_ENTRIES_PER_CUSTOMER, len(transactions)),
    )
    entries = []

    for index in range(target_count):
        transaction = transactions[index % len(transactions)]
        transaction_date = parse_date(transaction["date"])
        shopping_date = transaction_date + timedelta(
            days=DATE_OFFSETS[index % len(DATE_OFFSETS)]
        )
        amount = round(
            transaction["amount"] * AMOUNT_FACTORS[index % len(AMOUNT_FACTORS)],
            2,
        )

        entries.append(
            {
                "customerId": customer_id,
                "merchant": MERCHANTS[index % len(MERCHANTS)],
                "amount": amount,
                "date": shopping_date.strftime("%Y-%m-%d"),
                "category": CATEGORIES[index % len(CATEGORIES)],
            }
        )

    return entries


def validate_shopping_data(
    customers: list[dict[str, Any]],
    transactions_by_customer: dict[int, list[dict[str, Any]]],
    shopping_records: list[dict[str, Any]],
) -> None:
    customer_ids = {int(customer["customerId"]) for customer in customers}

    for record in shopping_records:
        customer_id = int(record["customerId"])
        if customer_id not in customer_ids:
            raise ValueError(f"Unknown shopping customerId: {customer_id}")

        related_transactions = transactions_by_customer.get(customer_id, [])
        related_dates = {transaction["date"] for transaction in related_transactions}
        close_dates = {
            (parse_date(date) + timedelta(days=offset)).strftime("%Y-%m-%d")
            for date in related_dates
            for offset in range(-2, 3)
        }
        if record["date"] not in close_dates:
            raise ValueError(
                f"Shopping date {record['date']} is not close to IBM dates "
                f"for customerId {customer_id}"
            )


def main() -> None:
    customers = load_json(IBM_DIR / "customers.json")
    raw_transactions = load_json(IBM_DIR / "transactions.json")
    transactions = [normalize_transaction(transaction) for transaction in raw_transactions]

    transactions_by_customer: dict[int, list[dict[str, Any]]] = {}
    for transaction in transactions:
        transactions_by_customer.setdefault(transaction["customerId"], []).append(transaction)

    shopping_records = []
    for customer in sorted(customers, key=lambda item: int(item["customerId"])):
        customer_id = int(customer["customerId"])
        shopping_records.extend(
            generate_entries(customer_id, transactions_by_customer.get(customer_id, []))
        )

    validate_shopping_data(customers, transactions_by_customer, shopping_records)
    write_json(OUTPUT_FILE, shopping_records)
    print(f"Generated {len(shopping_records)} shopping records at {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
