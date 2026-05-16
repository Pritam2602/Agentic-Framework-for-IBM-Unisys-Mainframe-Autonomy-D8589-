"""Import AWS CardDemo sample data into the local IBM JSON shape.

This script implements the "option 1" integration path:

1. Clone or download https://github.com/aws-samples/aws-mainframe-modernization-carddemo.
2. Read the repository's ASCII sample data files.
3. Convert CardDemo fixed-width records into this project's JSON contracts:
   - data/ibm/customers.json
   - data/ibm/accounts.json
   - data/ibm/transactions.json
4. Optionally regenerate data/unisys/shopping.json from the imported IBM
   transactions so federation demos still have matching enrichment records.

The script uses the ASCII files shipped by CardDemo instead of EBCDIC files so
it can run on a normal developer machine without mainframe transfer tooling.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / ".tmp_carddemo"
DEFAULT_REPO = "https://github.com/aws-samples/aws-mainframe-modernization-carddemo.git"
IBM_DIR = ROOT / "data" / "ibm"

ZONED_DIGITS = {
    "{": ("0", 1),
    "A": ("1", 1),
    "B": ("2", 1),
    "C": ("3", 1),
    "D": ("4", 1),
    "E": ("5", 1),
    "F": ("6", 1),
    "G": ("7", 1),
    "H": ("8", 1),
    "I": ("9", 1),
    "}": ("0", -1),
    "J": ("1", -1),
    "K": ("2", -1),
    "L": ("3", -1),
    "M": ("4", -1),
    "N": ("5", -1),
    "O": ("6", -1),
    "P": ("7", -1),
    "Q": ("8", -1),
    "R": ("9", -1),
}


def text(value: str) -> str:
    return " ".join(value.strip().split())


def int_text(value: str, default: int = 0) -> int:
    stripped = value.strip()
    return int(stripped) if stripped else default


def parse_zoned_decimal(value: str, scale: int = 2) -> float:
    """Parse DISPLAY signed zoned decimal values such as 0000005047G."""
    stripped = value.strip()
    if not stripped:
        return 0.0

    last = stripped[-1]
    if last in ZONED_DIGITS:
        digit, sign = ZONED_DIGITS[last]
        digits = stripped[:-1] + digit
    else:
        sign = -1 if stripped.startswith("-") else 1
        digits = stripped.lstrip("+-")

    digits = "".join(ch for ch in digits if ch.isdigit()) or "0"
    return round(sign * (int(digits) / (10**scale)), scale)


def iter_fixed(path: Path, record_length: int) -> Iterable[str]:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if len(line) < record_length:
            raise ValueError(f"{path.name} has short record: expected {record_length}, got {len(line)}")
        yield line[:record_length]


def source_data_dir(source: Path) -> Path:
    data_dir = source / "app" / "data" / "ASCII"
    required = ["custdata.txt", "acctdata.txt", "cardxref.txt", "dailytran.txt"]
    missing = [name for name in required if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing CardDemo ASCII data files under {data_dir}: {', '.join(missing)}"
        )
    return data_dir


def ensure_source(source: Path, repo: str) -> None:
    if source_data_exists(source):
        return
    subprocess.run(
        ["git", "clone", "--depth", "1", repo, str(source)],
        cwd=ROOT,
        check=True,
    )


def source_data_exists(source: Path) -> bool:
    try:
        source_data_dir(source)
    except FileNotFoundError:
        return False
    return True


def parse_customers(data_dir: Path) -> list[dict[str, Any]]:
    customers: list[dict[str, Any]] = []
    for record in iter_fixed(data_dir / "custdata.txt", 500):
        customer_id = int_text(record[0:9])
        first = text(record[9:34])
        middle = text(record[34:59])
        last = text(record[59:84])
        full_name = " ".join(part for part in [first, middle, last] if part)
        customers.append(
            {
                "customerId": customer_id,
                "customerName": full_name or f"Customer {customer_id}",
                "sourceDataset": "AWS.M2.CARDDEMO.CUSTDATA.PS",
                "firstName": first,
                "middleName": middle,
                "lastName": last,
                "state": text(record[234:236]),
                "country": text(record[236:239]),
                "zip": text(record[239:249]),
                "phone": text(record[249:264]),
                "creditScore": int_text(record[329:332]),
            }
        )
    return customers


def parse_card_xref(data_dir: Path) -> dict[str, dict[str, int]]:
    xref: dict[str, dict[str, int]] = {}
    for record in iter_fixed(data_dir / "cardxref.txt", 36):
        card_num = text(record[0:16])
        xref[card_num] = {
            "customerId": int_text(record[16:25]),
            "accountId": int_text(record[25:36]),
        }
    return xref


def parse_accounts(data_dir: Path, xref_by_account: dict[int, int]) -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    for record in iter_fixed(data_dir / "acctdata.txt", 300):
        account_id = int_text(record[0:11])
        customer_id = xref_by_account.get(account_id)
        accounts.append(
            {
                "accountNumber": f"ACCT-{account_id:011d}",
                "accountId": account_id,
                "customerId": customer_id,
                "sourceDataset": "AWS.M2.CARDDEMO.ACCTDATA.PS",
                "activeStatus": text(record[11:12]),
                "currentBalance": parse_zoned_decimal(record[12:24]),
                "creditLimit": parse_zoned_decimal(record[24:36]),
                "cashCreditLimit": parse_zoned_decimal(record[36:48]),
                "openDate": text(record[48:58]),
                "expirationDate": text(record[58:68]),
                "reissueDate": text(record[68:78]),
                "currentCycleCredit": parse_zoned_decimal(record[78:90]),
                "currentCycleDebit": parse_zoned_decimal(record[90:102]),
                "zip": text(record[102:112]),
                "groupId": text(record[112:122]),
            }
        )
    return accounts


def parse_transactions(data_dir: Path, xref_by_card: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    transactions: list[dict[str, Any]] = []
    for record in iter_fixed(data_dir / "dailytran.txt", 350):
        card_num = text(record[262:278])
        xref = xref_by_card.get(card_num, {})
        amount = parse_zoned_decimal(record[132:143])
        original_ts = text(record[278:304])
        transaction_date = original_ts[:10] if len(original_ts) >= 10 else ""
        transaction_id = text(record[0:16])

        transactions.append(
            {
                "transactionId": f"TXN-{transaction_id}",
                "customerId": xref.get("customerId"),
                "accountId": xref.get("accountId"),
                "cardNumber": card_num,
                "amount": amount,
                "transactionAmount": amount,
                "date": transaction_date,
                "transactionDate": transaction_date,
                "transactionType": "CREDIT" if amount < 0 else "DEBIT",
                "sourceDataset": "AWS.M2.CARDDEMO.DALYTRAN.PS",
                "transactionCode": text(record[16:18]),
                "categoryCode": text(record[18:22]),
                "source": text(record[22:32]),
                "description": text(record[32:132]),
                "merchantId": int_text(record[143:152]),
                "merchant": text(record[152:202]),
                "merchantCity": text(record[202:252]),
                "merchantZip": text(record[252:262]),
                "originalTimestamp": original_ts,
                "processedTimestamp": text(record[304:330]),
            }
        )

    return [item for item in transactions if item.get("customerId") is not None]


def write_json(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=4) + "\n", encoding="utf-8")


def import_carddemo(source: Path, repo: str, regenerate_shopping: bool) -> None:
    ensure_source(source, repo)
    data_dir = source_data_dir(source)

    customers = parse_customers(data_dir)
    xref_by_card = parse_card_xref(data_dir)
    xref_by_account = {
        item["accountId"]: item["customerId"]
        for item in xref_by_card.values()
    }
    accounts = parse_accounts(data_dir, xref_by_account)
    transactions = parse_transactions(data_dir, xref_by_card)

    write_json(IBM_DIR / "customers.json", customers)
    write_json(IBM_DIR / "accounts.json", accounts)
    write_json(IBM_DIR / "transactions.json", transactions)

    print(f"Imported {len(customers)} customers")
    print(f"Imported {len(accounts)} accounts")
    print(f"Imported {len(transactions)} transactions")

    if regenerate_shopping:
        subprocess.run(["python", "generate_shopping_data.py"], cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import AWS CardDemo sample data to local IBM JSON.")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Path to a cloned aws-mainframe-modernization-carddemo repo.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help="Git repo URL used if --source is missing.",
    )
    parser.add_argument(
        "--no-shopping",
        action="store_true",
        help="Do not regenerate Unisys shopping enrichment after import.",
    )
    args = parser.parse_args()
    import_carddemo(
        source=args.source,
        repo=args.repo,
        regenerate_shopping=not args.no_shopping,
    )


if __name__ == "__main__":
    main()
