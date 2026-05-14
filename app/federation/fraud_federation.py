"""Fraud and Risk federation logic.

Use case (HANDOFF.md #4 Fraud and Risk Detection):
    IBM/Zowe provides the financial transactions (the authoritative ledger).
    Unisys/ePortal provides the behavioral context (merchant, category,
    cart status, browsing time, loyalty) that helps decide whether a
    transaction looks genuine.

This module DOES NOT modify IBM amounts. It joins each IBM transaction
to the Unisys shopping records for the same customer + date and applies
a set of explainable risk rules. Every signal carries its own weight,
evidence, and human-readable reason so the federated answer is auditable.
"""

from __future__ import annotations

import statistics
from typing import Any, Dict, List, Optional

from app.federation.shopping_federation import (
    IBM_TRANSACTIONS,
    UNISYS_SHOPPING,
    filter_ibm_transactions,
    filter_unisys_shopping,
    load_json,
    transaction_amount,
    transaction_date,
)


HIGH_VALUE_ABSOLUTE = 10_000.0
HIGH_VALUE_RATIO = 3.0
INSTANT_SPEND_BROWSING_THRESHOLD = 5
ABANDONED_CART_RATIO = 1.5
MISSING_CONTEXT_THRESHOLD = 5_000.0

RISK_BAND_HIGH = 0.60
RISK_BAND_MEDIUM = 0.30


def _customer_baseline(customer_history: List[Dict[str, Any]]) -> Dict[str, float]:
    amounts = [transaction_amount(record) for record in customer_history]
    if not amounts:
        return {"avg": 0.0, "stddev": 0.0, "max": 0.0, "count": 0.0}
    avg = round(statistics.fmean(amounts), 2)
    stddev = round(statistics.pstdev(amounts), 2) if len(amounts) > 1 else 0.0
    return {
        "avg": avg,
        "stddev": stddev,
        "max": round(max(amounts), 2),
        "count": float(len(amounts)),
    }


def _verdict_for_score(score: float) -> str:
    if score >= RISK_BAND_HIGH:
        return "likely_fraud"
    if score >= RISK_BAND_MEDIUM:
        return "suspicious"
    return "genuine"


def _risk_band(score: float) -> str:
    if score >= RISK_BAND_HIGH:
        return "high"
    if score >= RISK_BAND_MEDIUM:
        return "medium"
    return "low"


def _evaluate_transaction(
    txn: Dict[str, Any],
    same_day_shopping: List[Dict[str, Any]],
    baseline: Dict[str, float],
) -> Dict[str, Any]:
    amount = transaction_amount(txn)
    date = transaction_date(txn)
    avg = baseline.get("avg", 0.0)

    signals: List[Dict[str, Any]] = []
    score = 0.0

    if amount >= HIGH_VALUE_ABSOLUTE or (avg and amount >= avg * HIGH_VALUE_RATIO):
        weight = 0.35
        score += weight
        signals.append(
            {
                "rule": "high_value_outlier",
                "weight": weight,
                "severity": "high",
                "evidence": {
                    "amount": amount,
                    "customer_avg": avg,
                    "ratio_to_avg": round(amount / avg, 2) if avg else None,
                    "threshold_absolute": HIGH_VALUE_ABSOLUTE,
                },
                "reason": (
                    "Transaction amount is significantly above the customer's typical "
                    "spend baseline or exceeds the global high-value threshold."
                ),
            }
        )

    if not same_day_shopping and amount >= MISSING_CONTEXT_THRESHOLD:
        weight = 0.25
        score += weight
        signals.append(
            {
                "rule": "missing_behavioral_context",
                "weight": weight,
                "severity": "medium",
                "evidence": {
                    "amount": amount,
                    "unisys_records_for_date": 0,
                    "threshold_amount": MISSING_CONTEXT_THRESHOLD,
                },
                "reason": (
                    "A material IBM charge was posted on a date with no Unisys "
                    "shopping behavior — no merchant, browsing, or cart signal "
                    "supports it."
                ),
            }
        )

    abandoned_or_wishlisted = [
        record
        for record in same_day_shopping
        if str(record.get("cartStatus", "")).lower() in {"abandoned", "wishlisted"}
    ]
    if abandoned_or_wishlisted and amount >= max(avg * ABANDONED_CART_RATIO, 1.0):
        weight = 0.25
        score += weight
        signals.append(
            {
                "rule": "abandoned_cart_with_charge",
                "weight": weight,
                "severity": "high",
                "evidence": {
                    "amount": amount,
                    "customer_avg": avg,
                    "ratio_to_avg": round(amount / avg, 2) if avg else None,
                    "carts": [
                        {
                            "merchant": record.get("merchant"),
                            "cartStatus": record.get("cartStatus"),
                            "amount": record.get("amount"),
                        }
                        for record in abandoned_or_wishlisted
                    ],
                },
                "reason": (
                    "IBM recorded a charge on a date where the user's Unisys cart "
                    "activity shows only abandoned or wishlisted carts."
                ),
            }
        )

    total_browsing = sum(
        int(record.get("browsingSessionMinutes", 0) or 0)
        for record in same_day_shopping
    )
    if (
        same_day_shopping
        and avg
        and amount >= avg * 2
        and total_browsing <= INSTANT_SPEND_BROWSING_THRESHOLD
    ):
        weight = 0.15
        score += weight
        signals.append(
            {
                "rule": "instant_high_spend",
                "weight": weight,
                "severity": "medium",
                "evidence": {
                    "amount": amount,
                    "customer_avg": avg,
                    "total_browsing_minutes": total_browsing,
                    "browsing_threshold": INSTANT_SPEND_BROWSING_THRESHOLD,
                },
                "reason": (
                    "Large charge paired with very short browsing session — "
                    "spend pattern does not match typical pre-purchase research."
                ),
            }
        )

    unisys_total = round(
        sum(float(record.get("amount", 0) or 0) for record in same_day_shopping),
        2,
    )
    if (
        same_day_shopping
        and unisys_total
        and amount >= unisys_total * 2
    ):
        weight = 0.20
        score += weight
        signals.append(
            {
                "rule": "ibm_unisys_amount_divergence",
                "weight": weight,
                "severity": "medium",
                "evidence": {
                    "ibm_amount": amount,
                    "unisys_observed_total": unisys_total,
                    "delta": round(amount - unisys_total, 2),
                },
                "reason": (
                    "IBM ledger value is substantially higher than Unisys-observed "
                    "shopping activity on the same date — possible unauthorized "
                    "charge layered on top of legitimate behavior."
                ),
            }
        )

    score = round(min(score, 1.0), 3)

    return {
        "transactionId": txn.get("transactionId"),
        "customerId": txn.get("customerId"),
        "amount": amount,
        "date": date,
        "transactionType": txn.get("transactionType"),
        "risk_score": score,
        "risk_band": _risk_band(score),
        "verdict": _verdict_for_score(score),
        "fraud_signals": signals,
        "supporting_context": {
            "unisys_event_count": len(same_day_shopping),
            "unisys_observed_amount_total": unisys_total,
            "browsing_minutes_total": total_browsing,
            "merchants": sorted(
                {str(record.get("merchant")) for record in same_day_shopping if record.get("merchant")}
            ),
            "cart_statuses": sorted(
                {str(record.get("cartStatus")) for record in same_day_shopping if record.get("cartStatus")}
            ),
        },
    }


def assess_transaction_risk(
    customer_id: int,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a fraud and risk assessment for a customer over IBM + Unisys data.

    Args:
        customer_id: customer to score.
        date: optional YYYY-MM-DD filter for the transactions evaluated. The
              behavioral baseline always uses the full customer history so
              that single-day evaluations remain comparable to the norm.

    Returns:
        Dict containing per-transaction verdicts, summary counts, and
        explainable signals.
    """
    ibm_records = load_json(IBM_TRANSACTIONS)
    unisys_records = load_json(UNISYS_SHOPPING)

    full_history = filter_ibm_transactions(ibm_records, customer_id, None)
    txns_in_window = filter_ibm_transactions(ibm_records, customer_id, date)
    unisys_in_window = filter_unisys_shopping(unisys_records, customer_id, date)

    baseline = _customer_baseline(full_history)

    unisys_by_date: Dict[str, List[Dict[str, Any]]] = {}
    for record in filter_unisys_shopping(unisys_records, customer_id, None):
        unisys_by_date.setdefault(str(record.get("date")), []).append(record)

    evaluated: List[Dict[str, Any]] = []
    for txn in txns_in_window:
        same_day = unisys_by_date.get(transaction_date(txn), [])
        evaluated.append(_evaluate_transaction(txn, same_day, baseline))

    band_counts = {"high": 0, "medium": 0, "low": 0}
    verdict_counts = {"likely_fraud": 0, "suspicious": 0, "genuine": 0}
    total_amount_at_risk = 0.0
    flagged_signals: Dict[str, int] = {}
    for item in evaluated:
        band_counts[item["risk_band"]] = band_counts.get(item["risk_band"], 0) + 1
        verdict_counts[item["verdict"]] = verdict_counts.get(item["verdict"], 0) + 1
        if item["risk_band"] != "low":
            total_amount_at_risk += float(item["amount"])
        for signal in item["fraud_signals"]:
            rule = signal["rule"]
            flagged_signals[rule] = flagged_signals.get(rule, 0) + 1

    portfolio_score = (
        round(
            sum(item["risk_score"] for item in evaluated) / len(evaluated),
            3,
        )
        if evaluated
        else 0.0
    )

    return {
        "view_id": "fraud_risk_assessment",
        "customerId": customer_id,
        "date_filter": date,
        "summary": {
            "transactions_evaluated": len(evaluated),
            "portfolio_risk_score": portfolio_score,
            "portfolio_risk_band": _risk_band(portfolio_score),
            "risk_band_counts": band_counts,
            "verdict_counts": verdict_counts,
            "amount_at_risk": round(total_amount_at_risk, 2),
            "flagged_signal_counts": flagged_signals,
            "unisys_events_in_window": len(unisys_in_window),
        },
        "customer_baseline": baseline,
        "rules_applied": [
            {
                "rule": "high_value_outlier",
                "weight": 0.35,
                "trigger": (
                    "amount >= $10,000 OR amount >= customer_avg * 3 — large outlier vs ledger history."
                ),
            },
            {
                "rule": "missing_behavioral_context",
                "weight": 0.25,
                "trigger": (
                    f"amount >= ${int(MISSING_CONTEXT_THRESHOLD)} AND no Unisys shopping events on the same date."
                ),
            },
            {
                "rule": "abandoned_cart_with_charge",
                "weight": 0.25,
                "trigger": (
                    "Unisys shows only abandoned/wishlisted carts on the same date as a meaningful IBM charge."
                ),
            },
            {
                "rule": "instant_high_spend",
                "weight": 0.15,
                "trigger": (
                    "amount >= customer_avg * 2 AND total browsing minutes for the date <= 5."
                ),
            },
            {
                "rule": "ibm_unisys_amount_divergence",
                "weight": 0.20,
                "trigger": (
                    "IBM amount >= 2x the Unisys observed amount total for the same date "
                    "(behavior does not justify the ledger entry)."
                ),
            },
        ],
        "evaluations": evaluated,
        "sources": ["IBM CardDemo", "Unisys ePortal"],
        "join_key": "customerId + date",
        "guardrails": [
            "IBM remains the financial authority — risk scoring does not modify amounts.",
            "Unisys amounts mirror IBM and are used here only as behavioral evidence.",
            "Verdicts are explainable: every score lists the rules that contributed.",
        ],
    }


if __name__ == "__main__":
    import json

    result = assess_transaction_risk(customer_id=103)
    print(json.dumps(result, indent=2))
