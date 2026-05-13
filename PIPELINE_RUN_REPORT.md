# Pipeline Run Report

## Test Query

```text
show total spend for customer 101 on 2026-03-10 with shopping behavior
```

Run mode: `enable_llm=false`, `safe_mock` execution.

This means the pipeline used deterministic agent fallbacks and the local mock z/OS
simulator instead of calling a live LLM or real z/OS.

---

## Overall Result

| Field | Output |
| --- | --- |
| Pipeline stage | `consumer_ready` |
| Next stage | `consumer_layer` |
| Execution status | `completed` |
| Normalized records | `4` |
| Top federated view | `Customer Spend with Behavioral Context` |
| Overall federation confidence | `92.5%` |
| Final total spend | `2000.0` |
| Reconciliation status | `matched` |

Final summary returned by the pipeline:

```text
Query: show total spend for customer 101 on 2026-03-10 with shopping behavior
Intent: analyze on shopping, transaction (confidence: 80%)
Output: aggregate | Metric: total_spend | Aggregation: sum | Federation required
Context: IBM: CBTRN03C -> AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS | Unisys: /api/unisys/shopping (confidence: 92%)
Planning: completed | Steps: 2
Execution: completed | Normalized records: 4
Federation: 3 relationships found | Top view: 'Customer Spend with Behavioral Context' | Confidence: 92%
```

---

## 1. Intent Agent Output

The Intent Agent interpreted the query as an analytical, federated total-spend
request.

| Field | Output |
| --- | --- |
| Task | `analyze` |
| Entities | `shopping`, `transaction` |
| Attributes | `spend` |
| Systems | `unisys`, `ibm` |
| Metric | `total_spend` |
| Aggregation | `sum` |
| Output mode | `aggregate` |
| Requires federation | `true` |
| Priority | `high` |
| Confidence | `0.8` |

Filters:

```json
{
  "time_range": {
    "start": "2026-03-10",
    "end": "2026-03-10"
  },
  "conditions": [
    { "field": "customerId", "value": 101 },
    { "field": "customerId", "value": 101 },
    { "field": "date", "value": "2026-03-10" }
  ]
}
```

Note: `customerId` appears twice in the extracted conditions. This does not break
execution because downstream parameter extraction collapses it to `customerId=101`.

---

## 2. Context Resolution Agent Output

The Context Resolution Agent located both IBM and Unisys sources.

### IBM Context

| Field | Output |
| --- | --- |
| Program | `CBTRN03C` |
| Dataset | `AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS` |
| JCL job | `TRANREPT` |
| Confidence | `0.92` |

Relevant IBM reasoning:

```text
Total spend requires combining IBM transaction data with Unisys shopping data using customerId as join key and date alignment
```

### Unisys Context

| Field | Output |
| --- | --- |
| API | `/api/unisys/shopping` |
| Tool | `get_shopping_data` |
| Entity | `shopping` |
| Fields | `customerId`, `merchant`, `amount`, `date`, `category`, `loyaltyPoints`, `browsingSessionMinutes`, `cartStatus`, `merchantCategory` |

Cross-system mapping:

```json
{
  "customerId": "customerId",
  "date": "transactionDate",
  "amount": "transactionAmount"
}
```

Warning:

```text
LLM unavailable - used rule-based fallback resolution
```

---

## 3. Planner Agent Output

The Planner Agent created a two-step execution plan and selected Zowe catalog
commands for IBM access.

Planner objective:

```text
analyze | shopping, transaction | metric=total_spend | aggregation=sum
```

Planner strategy:

```text
Fetch IBM financial records first, fetch Unisys behavioral enrichment second, then normalize both outputs for federation.
```

### Selected Zowe Commands

| Command ID | Zowe command | Category | Operation | Cost | Confidence |
| --- | --- | --- | --- | --- | --- |
| `cmd-015` | `zowe files view ds` | `data` | `READ` | `MEDIUM` | `0.95` |
| `cmd-012` | `zowe files list ds` | `metadata` | `READ` | `LOW` | `0.97` |

### Planner Steps

| Order | System | Action | Command / Endpoint |
| --- | --- | --- | --- |
| 1 | IBM | `fetch transactions` | `zowe files view ds "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS"` |
| 2 | Unisys | `fetch shopping enrichment` | `/api/unisys/shopping` |

Governance controls produced by the Planner:

- `safe_mock execution mode unless explicitly switched to allowlisted`
- `source lineage must be preserved for every normalized field`
- `customerId is the preferred cross-system join key`
- `IBM transaction amounts remain the financial authority`
- `Unisys amounts must not be added to IBM spend totals`

---

## 4. Execution Agent Output

Execution completed successfully:

```text
Execution completed. 2/2 executed step(s) completed successfully.
```

### Step 1: IBM Mock z/OS Dataset Read

| Field | Output |
| --- | --- |
| Step ID | `fetch-ibm-transactions` |
| System | `ibm` |
| Status | `completed` |
| Command | `zowe files view ds "AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS"` |
| Platform | `IBM z/OS` |
| Dataset | `AWS.M2.CARDDEMO.TRANSACT.VSAM.KSDS` |
| Records returned | `1` |

Mock z/OS spool output:

```text
MOCK Z/OS READ 1 TRANSACTION RECORD(S)
```

IBM record returned:

```json
{
  "transactionId": "TXN-20260310-101-001",
  "customerId": 101,
  "amount": 2000.0,
  "date": "2026-03-10",
  "transactionType": "DEBIT"
}
```

### Step 2: Unisys ePortal Shopping Enrichment

| Field | Output |
| --- | --- |
| Step ID | `fetch-unisys-shopping` |
| System | `unisys` |
| Status | `completed` |
| Endpoint | `/api/unisys/shopping` |
| Records returned | `3` |

Unisys records returned:

```json
[
  {
    "customerId": 101,
    "merchant": "Amazon",
    "amount": 1200.0,
    "date": "2026-03-10",
    "category": "electronics",
    "loyaltyPoints": 120,
    "browsingSessionMinutes": 12,
    "cartStatus": "completed",
    "merchantCategory": "electronics_premium"
  },
  {
    "customerId": 101,
    "merchant": "Zomato",
    "amount": 500.0,
    "date": "2026-03-10",
    "category": "shopping",
    "loyaltyPoints": 50,
    "browsingSessionMinutes": 3,
    "cartStatus": "completed",
    "merchantCategory": "groceries"
  },
  {
    "customerId": 101,
    "merchant": "Uber",
    "amount": 300.0,
    "date": "2026-03-10",
    "category": "electronics",
    "loyaltyPoints": 95,
    "browsingSessionMinutes": 8,
    "cartStatus": "wishlisted",
    "merchantCategory": "ride_hailing"
  }
]
```

---

## 5. Normalization Agent Output

The Normalization Agent converted execution outputs into canonical records.

| Field | Output |
| --- | --- |
| Total records | `4` |
| IBM records | `1` |
| Unisys records | `3` |
| Canonical entities | `shopping`, `transaction` |

Normalization warning:

```text
Do not add Unisys amount to IBM amount for spend totals; Unisys is enrichment.
```

Normalized record breakdown:

| Source | Entity | Count |
| --- | --- | --- |
| IBM | `transaction` | `1` |
| Unisys | `shopping` | `3` |

---

## 6. Federation Intelligence Output

Federation Intelligence consumed the normalized records and recommended the best
business view.

| Field | Output |
| --- | --- |
| Top view | `Customer Spend with Behavioral Context` |
| View ID | `customer_spend_enriched` |
| Relationships discovered | `3` |
| Views evaluated | `5` |
| Overall confidence | `0.925` |

Reasoning:

```text
Intent: analyze on entities ['shopping', 'transaction'] for metric total_spend.
Entity relationships discovered: ibm.transaction -> unisys.shopping via customerId (enrichment);
ibm.account -> unisys.shopping via customerId (reference).
Top recommended view: 'Customer Spend with Behavioral Context'.
IBM CardDemo is the financial authority; Unisys ePortal adds behavioral enrichment only.
Federation was executed and results are included in this response.
```

### Final Federated Result

| Metric | Output |
| --- | --- |
| IBM authoritative total spend | `2000.0` |
| IBM transaction count | `1` |
| Unisys enrichment count | `3` |
| Unisys observed amount total | `2000.0` |
| Variance | `0.0` |
| Reconciliation status | `matched` |

Merchant observed amounts:

| Merchant | Observed amount |
| --- | --- |
| Amazon | `1200.0` |
| Zomato | `500.0` |
| Uber | `300.0` |

Category observed amounts:

| Category | Observed amount |
| --- | --- |
| electronics | `1500.0` |
| shopping | `500.0` |

Behavioral enrichment:

| Field | Output |
| --- | --- |
| Total loyalty points | `265` |
| Cart status breakdown | `completed: 2`, `wishlisted: 1` |
| Total browsing minutes | `23` |

Reconciliation rule:

```text
Use IBM amount for total_spend; use Unisys amount only as observed behavior/enrichment.
```

---

## 7. Governance Output

| Field | Output |
| --- | --- |
| Financial authority | `IBM CardDemo` |
| Enrichment authority | `Unisys ePortal` |
| Join key | `customerId` |
| Double-counting protected | `true` |
| Federation executed | `true` |
| Consumed normalization output | `true` |
| Normalized record count | `4` |
| LLM refinement | `disabled` |

Amount reconciliation:

```json
{
  "status": "matched",
  "ibm_authoritative_total": 2000.0,
  "unisys_observed_total": 2000.0,
  "variance": 0.0,
  "warning": null,
  "rule": "Use IBM amount for total_spend; use Unisys amount only as observed behavior/enrichment."
}
```

---

## Conclusion

The application successfully processed the query end to end:

```text
Intent -> Context -> Planner -> Execution -> Normalization -> Federation Intelligence -> Consumer
```

The final answer is:

```text
Customer 101 spent 2000.0 on 2026-03-10.
```

That total comes from IBM CardDemo only. Unisys provided shopping behavior
enrichment for Amazon, Zomato, and Uber. The Unisys observed amount total now
matches IBM at `2000.0`, and reconciliation status is `matched`.
