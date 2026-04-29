"""Executes a federated view by invoking the appropriate federation functions."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.federation.shopping_federation import (
    federate_customer_spend,
    category_analysis,
    loyalty_summary,
    cart_analysis,
    browsing_summary,
    behavior_insights,
    filter_ibm_transactions,
    filter_unisys_shopping,
    load_json,
    IBM_TRANSACTIONS,
    UNISYS_SHOPPING,
)


def execute_view(
    view_id: str,
    customer_id: int,
    date: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a named federated view for a given customer (and optional date)."""

    if view_id == "customer_spend_enriched":
        return _customer_spend_enriched(customer_id, date)
    elif view_id == "merchant_category_spend":
        return _merchant_category_spend(customer_id, date)
    elif view_id == "loyalty_spend_correlation":
        return _loyalty_spend_correlation(customer_id, date)
    elif view_id == "cart_conversion_analysis":
        return _cart_conversion_analysis(customer_id, date)
    elif view_id == "browsing_to_spend_funnel":
        return _browsing_to_spend_funnel(customer_id, date)
    else:
        return _customer_spend_enriched(customer_id, date)


def _customer_spend_enriched(customer_id: int, date: Optional[str]) -> Dict[str, Any]:
    base = federate_customer_spend(customer_id, date)
    base["view_id"] = "customer_spend_enriched"
    return base


def _merchant_category_spend(customer_id: int, date: Optional[str]) -> Dict[str, Any]:
    ibm = filter_ibm_transactions(load_json(IBM_TRANSACTIONS), customer_id, date)
    unisys = filter_unisys_shopping(load_json(UNISYS_SHOPPING), customer_id, date)

    ibm_total = round(sum(float(r.get("amount", r.get("transactionAmount", 0))) for r in ibm), 2)
    cat = category_analysis(unisys)

    merchant_detail: Dict[str, Dict[str, Any]] = {}
    for rec in unisys:
        m = rec.get("merchant", "unknown")
        if m not in merchant_detail:
            merchant_detail[m] = {"category": rec.get("category"), "events": 0}
        merchant_detail[m]["events"] += 1

    return {
        "view_id": "merchant_category_spend",
        "customerId": customer_id,
        "date_filter": date,
        "ibm_total_spend": ibm_total,
        "spend_by_category": cat,
        "merchant_breakdown": merchant_detail,
        "sources": ["IBM CardDemo", "Unisys ePortal"],
        "join_key": "customerId",
        "spend_authority": "IBM CardDemo — amounts are NOT summed with Unisys",
    }


def _loyalty_spend_correlation(customer_id: int, date: Optional[str]) -> Dict[str, Any]:
    ibm = filter_ibm_transactions(load_json(IBM_TRANSACTIONS), customer_id, date)
    unisys = filter_unisys_shopping(load_json(UNISYS_SHOPPING), customer_id, date)

    ibm_total = round(sum(float(r.get("amount", r.get("transactionAmount", 0))) for r in ibm), 2)
    loyalty = loyalty_summary(unisys)

    points = loyalty["total_loyalty_points"]
    ratio = round(points / ibm_total, 4) if ibm_total else 0.0

    return {
        "view_id": "loyalty_spend_correlation",
        "customerId": customer_id,
        "date_filter": date,
        "ibm_total_spend": ibm_total,
        "loyalty": loyalty,
        "loyalty_per_dollar_spent": ratio,
        "sources": ["IBM CardDemo", "Unisys ePortal"],
        "join_key": "customerId",
    }


def _cart_conversion_analysis(customer_id: int, date: Optional[str]) -> Dict[str, Any]:
    ibm = filter_ibm_transactions(load_json(IBM_TRANSACTIONS), customer_id, date)
    unisys = filter_unisys_shopping(load_json(UNISYS_SHOPPING), customer_id, date)

    ibm_total = round(sum(float(r.get("amount", r.get("transactionAmount", 0))) for r in ibm), 2)
    cart = cart_analysis(unisys)
    browsing = browsing_summary(unisys)

    abandoned = [r for r in unisys if r.get("cartStatus") == "abandoned"]
    lost_opportunity = round(sum(float(r.get("amount", 0)) for r in abandoned), 2)

    return {
        "view_id": "cart_conversion_analysis",
        "customerId": customer_id,
        "date_filter": date,
        "ibm_confirmed_spend": ibm_total,
        "cart": cart,
        "browsing": browsing,
        "abandoned_browsing_value": lost_opportunity,
        "note": "abandoned_browsing_value is indicative — Unisys amounts mirror IBM and are not additive",
        "sources": ["IBM CardDemo", "Unisys ePortal"],
        "join_key": "customerId",
    }


def _browsing_to_spend_funnel(customer_id: int, date: Optional[str]) -> Dict[str, Any]:
    ibm = filter_ibm_transactions(load_json(IBM_TRANSACTIONS), customer_id, date)
    unisys = filter_unisys_shopping(load_json(UNISYS_SHOPPING), customer_id, date)

    ibm_total = round(sum(float(r.get("amount", r.get("transactionAmount", 0))) for r in ibm), 2)
    browsing = browsing_summary(unisys)

    spend_per_browse_minute = (
        round(ibm_total / browsing["total_browsing_minutes"], 2)
        if browsing["total_browsing_minutes"]
        else 0.0
    )

    funnel: list[Dict[str, Any]] = []
    for rec in sorted(unisys, key=lambda r: int(r.get("browsingSessionMinutes", 0)), reverse=True):
        funnel.append(
            {
                "merchant": rec.get("merchant"),
                "browsingMinutes": rec.get("browsingSessionMinutes"),
                "cartStatus": rec.get("cartStatus"),
                "category": rec.get("category"),
            }
        )

    return {
        "view_id": "browsing_to_spend_funnel",
        "customerId": customer_id,
        "date_filter": date,
        "ibm_total_spend": ibm_total,
        "browsing_summary": browsing,
        "spend_per_browse_minute": spend_per_browse_minute,
        "session_funnel": funnel,
        "sources": ["IBM CardDemo", "Unisys ePortal"],
        "join_key": "customerId",
    }
