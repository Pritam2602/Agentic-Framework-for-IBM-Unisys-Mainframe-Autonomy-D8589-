"""Smoke verification for the Fraud and Risk Detection use case.

This script exercises the new fraud federation path at three layers and
prints the key signals so a reviewer can confirm the integration without
booting the full stack.

  1. Direct call to ``app.federation.fraud_federation.assess_transaction_risk``
  2. Federation intelligence executor (``execute_view``)
  3. The full pipeline handler (``POST /api/pipeline/run``)

Run:
    python verify_fraud_use_case.py

LLM is disabled so the script runs offline using deterministic fraud rules.
"""

from __future__ import annotations

import sys

from app.federation.fraud_federation import assess_transaction_risk
from app.main import app
from federation_intelligence.executor import execute_view
from fastapi.testclient import TestClient


CUSTOMER_ID = 103


def _print_evaluations(result: dict) -> None:
    print(f"  view_id:         {result.get('view_id')}")
    print(f"  customerId:      {result.get('customerId')}")
    summary = result.get("summary", {})
    print(f"  band counts:     {summary.get('risk_band_counts')}")
    print(f"  verdict counts:  {summary.get('verdict_counts')}")
    print(f"  amount at risk:  {summary.get('amount_at_risk')}")
    print(f"  flagged rules:   {summary.get('flagged_signal_counts')}")
    print("  top evaluations:")
    evaluations = sorted(
        result.get("evaluations", []),
        key=lambda item: item["risk_score"],
        reverse=True,
    )
    for evaluation in evaluations[:3]:
        rules = [signal["rule"] for signal in evaluation["fraud_signals"]]
        print(
            f"    {evaluation['transactionId']:24}  "
            f"amount={evaluation['amount']:>9.2f}  "
            f"score={evaluation['risk_score']:.2f}  "
            f"band={evaluation['risk_band']:<6}  "
            f"verdict={evaluation['verdict']:<14}  "
            f"rules={rules}"
        )


def step_direct() -> dict:
    print("\n[1/3] Direct call: assess_transaction_risk(customer_id=103)")
    result = assess_transaction_risk(customer_id=CUSTOMER_ID)
    _print_evaluations(result)
    return result


def step_executor() -> dict:
    print("\n[2/3] Federation executor: execute_view('fraud_risk_assessment', 103)")
    result = execute_view("fraud_risk_assessment", customer_id=CUSTOMER_ID)
    _print_evaluations(result)
    return result


def step_pipeline() -> dict:
    print("\n[3/3] Full pipeline: 'Run fraud and risk assessment for customer 103'")
    client = TestClient(app)
    response = client.post(
        "/api/pipeline/run",
        json={
            "user_query": "Run fraud and risk assessment for customer 103",
            "enable_llm": False,
        },
    )
    response.raise_for_status()
    payload = response.json()
    federation = payload.get("federation_intelligence") or {}
    top_view = (federation.get("top_view") or {}).get("view_id")
    print(f"  pipeline_stage:  {payload.get('pipeline_stage')}")
    print(f"  request_id:      {payload.get('request_id')}")
    print(f"  top_view:        {top_view}")
    fraud_result = federation.get("federated_result") or {}
    _print_evaluations(fraud_result)
    suggested = federation.get("suggested_explorations") or []
    print(f"  suggestions:     {[s.get('id') for s in suggested]}")
    return fraud_result


def main() -> int:
    direct = step_direct()
    executor = step_executor()
    pipeline = step_pipeline()

    checks = {
        "direct produced high-band verdict": direct["summary"]["risk_band_counts"]["high"] >= 1,
        "executor produced high-band verdict": executor["summary"]["risk_band_counts"]["high"] >= 1,
        "pipeline routed to fraud_risk_assessment": pipeline.get("view_id") == "fraud_risk_assessment",
        "pipeline produced at least one fraud signal":
            sum(pipeline.get("summary", {}).get("flagged_signal_counts", {}).values()) > 0,
    }

    print("\n--- Verification summary ---")
    failures = 0
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
        if not ok:
            failures += 1

    if failures:
        print(f"\n{failures} check(s) failed")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
