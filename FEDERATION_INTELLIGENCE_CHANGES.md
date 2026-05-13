# Federation Intelligence Layer - Changes & Achievements

## Current Architecture

The Federation Intelligence Layer now follows the architecture from the shared diagram:

```text
Intent Agent
-> Context Resolution Agent
-> Planning Layer
-> Execution Layer
-> Normalization Layer
-> Federation Intelligence Layer
-> Consumer Layer
```

The repo now includes a local Planner Agent. `/api/pipeline/run` passes Intent and
Context output to the Planner Agent, then sends the planner output to the Execution
Agent, then to the Normalization Agent, and Federation Intelligence consumes the
Normalization Agent output.

---

## What Was Built

A working **LLM-backed Federation Intelligence Layer** that consumes normalized IBM
and Unisys records, identifies cross-system relationships, ranks federated business
views, builds a federation plan, produces lineage/governance metadata, and returns a
consumer-ready federated result.

The layer is grounded-first:

- deterministic logic builds relationships, candidate views, lineage, and governance;
- the LLM refines the best view selection, reasoning, confidence, and notes;
- the LLM can only choose from grounded candidate view IDs;
- IBM remains the financial authority and Unisys remains behavioral enrichment.

---

## Files Created

### `planner_agent/__init__.py`

Package entry point. Exports `PlannerAgent`, `PlannerOutput`, `PlannerStep`, and
the planner API request/response models.

### `planner_agent/schemas.py`

Defines the Planner Agent contract: a safe execution plan with ordered steps,
data dependencies, federation join keys, normalization requirements, governance
controls, warnings, and reasoning.

### `planner_agent/agent.py`

Builds a grounded execution plan from Intent and Context output.

- Creates IBM dataset and Unisys API steps when those systems are resolved.
- Selects relevant IBM access commands from the local Zowe command catalog.
- Includes catalog command metadata and rendered Zowe command text in the planner JSON.
- Produces the classic `execution_sequence`, `parallel_groups`,
  `estimated_duration_seconds`, and `rollback_plan` fields expected from an
  execution planner.
- Preserves extracted filters such as `customerId` and date.
- Marks `customerId` as the preferred federation join key.
- Adds governance controls for lineage, safe mock execution, IBM financial
  authority, and Unisys enrichment-only behavior.
- Optionally asks the LLM to refine strategy, reasoning, warnings, and governance
  notes without inventing new execution targets.

### `app/api/planner.py`

Adds Planner Agent endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/planner/run` | Creates a planner output from intent and context |
| `GET` | `/api/planner/health` | Planner health and capability check |

### `app/mock_zos/simulator.py`

Adds a local mock z/OS simulator for safe Zowe command execution without a real
mainframe. It parses common Zowe command strings and returns z/OS-like responses
from local mock data.

Supported examples:

- `zowe files view ds "..."`
- `zowe files list ds "..."`
- `zowe zos-jobs submit ...`
- `zowe zos-jobs list/view ...`
- `zowe zos-workflows list/view ...`
- `zowe zosmf info`

Dataset reads map CardDemo-style dataset names to local IBM JSON records.

### `app/api/mock_zos.py`

Adds mock z/OS endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/mock-zos/execute` | Simulates a Zowe command locally |
| `GET` | `/api/mock-zos/health` | Lists supported mock z/OS command families |

### `federation_intelligence/__init__.py`

Package entry point. Exports `run_federation_intelligence` and
`FederationIntelligenceOutput`.

### `federation_intelligence/schemas.py`

Defines the Federation Intelligence contract:

| Model | Purpose |
| --- | --- |
| `EntityRelationship` | Cross-system entity link with source/target systems, join key, relationship type, confidence, and reasoning |
| `FederatedView` | Candidate business view with IBM fields, Unisys enrichment fields, business value, score, and recommendation reason |
| `FederationPlan` | Join strategy, financial-authority rule, enrichment fields, execution steps, and double-counting guard |
| `LineageRecord` | Field-level source system/entity lineage |
| `FederationIntelligenceOutput` | Relationships, recommended views, top view, plan, federated result, lineage, governance, confidence, and reasoning |
| `FederationAnalyzeRequest` | Request body for `/api/federation/analyze`; now accepts `normalized_output` and `use_llm` |
| `FederationExecuteRequest` | Request body for `/api/federation/execute` |

### `federation_intelligence/entity_graph.py`

Builds relationship graphs across IBM and Unisys entities.

- Maintains known links such as `transaction -> shopping`, `account -> shopping`,
  and `customer -> shopping`.
- Uses `mock_eportal/entity_mapping.json` when available.
- Falls back to system-ownership inference when the exact relationship is not in
  the catalog.
- Resolves the common join key, usually `customerId`.

### `federation_intelligence/view_recommender.py`

Scores and ranks the federated view catalog.

Available views:

| view_id | Business question |
| --- | --- |
| `customer_spend_enriched` | IBM spend with Unisys behavioral context |
| `merchant_category_spend` | Spend grouped by merchant/category enrichment |
| `loyalty_spend_correlation` | Loyalty value compared with IBM spend |
| `cart_conversion_analysis` | Cart behavior and confirmed spend impact |
| `browsing_to_spend_funnel` | Browsing behavior versus spend |

Scoring weighs entity overlap, metric match, task type, federation requirement,
and dual-system presence.

### `federation_intelligence/executor.py`

Still supports direct execution of the 5 named federated views for a `customerId`
and optional date using `app/federation/shopping_federation.py`.

This direct execution path is retained for testing and backward compatibility.
The preferred pipeline path is now:

```text
Execution Agent -> Normalization Agent -> Federation Intelligence
```

### `federation_intelligence/agent.py`

Main orchestrator:

1. Reads normalized records from `normalized_output`.
2. Derives entities from normalized canonical records when available.
3. Builds entity relationships and candidate federated views.
4. Builds the federation plan and lineage.
5. Produces a federated result from normalized records.
6. Computes IBM-only total spend from normalized IBM records.
7. Treats normalized Unisys records as enrichment only.
8. Reports Unisys observed amount totals separately and flags reconciliation
   variance when Unisys enrichment amounts do not match the IBM financial total.
9. Adds governance metadata including `consumed_normalization_output`.
10. Optionally invokes the LLM to refine top view, reasoning, confidence, and notes.
11. Returns `FederationIntelligenceOutput`.

If `normalized_output` is not supplied, the agent can still fall back to direct
view execution when `execute=True` and a `customerId` filter exists.

---

## Files Modified

### `app/api/federation_intelligence.py`

Endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/federation/analyze` | Runs Federation Intelligence from intent, context, optional normalized output, and `use_llm` |
| `POST` | `/api/federation/execute` | Directly executes a named federated view |
| `GET` | `/api/federation/views` | Lists all federated view definitions |
| `GET` | `/api/federation/health` | Health and capability check |

### `app/api/pipeline.py`

`/api/pipeline/run` now orchestrates the full agent chain:

```text
Intent -> Context -> Planner -> Execution -> Normalization -> Federation Intelligence
```

`PipelineResponse` now includes:

- `planner_json`
- `execution`
- `normalization`
- `federation_intelligence`

The final pipeline stage is now `consumer_ready`, and `next_stage` is
`consumer_layer`.

### `app/execution/dataset_executor.py`

Added simulated IBM transaction fetching from `data/ibm/transactions.json`, filtered
by `customerId` and date. This lets Execution Agent return real mock IBM records for
Normalization Agent to canonicalize.

### `execution_agent/agent.py`

Recognizes transaction-fetch planner steps as IBM dataset work.

In `safe_mock` mode, Zowe command strings from the Planner Agent are now routed
through the mock z/OS simulator instead of requiring a real z/OS connection.

### `normalization_agent/agent.py`

Deduplicates canonical records so federation totals are not inflated when the
execution response contains both step-level results and aggregated canonical output.

### `app/main.py`

Registers all relevant routers:

- `/api/execution/*`
- `/api/normalization/*`
- `/api/federation/*`

### Frontend

Updated the execution page to show the expanded flow:

```text
Intent -> Context -> Planner -> Execution -> Normalization -> Federation
```

The frontend now stores and displays:

- planner output;
- execution status;
- normalized record count;
- federation top view and full federation output.

---

## Role of Federation Intelligence

Federation Intelligence is no longer just a shortcut after context resolution.
Its intended role is now:

- consume normalized IBM and Unisys records;
- discover entity relationships;
- choose join keys;
- recommend federated business views;
- combine canonical records into a business-ready output;
- preserve lineage;
- enforce governance and double-counting rules;
- provide LLM-generated reasoning over grounded candidates.

Critical rule:

```text
total_spend = SUM(normalized IBM amounts only)
```

Unisys shopping amounts are not added to IBM amounts. They provide enrichment such as
merchant, category, loyalty points, browsing minutes, cart status, and merchant
category.

---

## LLM Behaviour

Federation Intelligence uses the same LLM pattern as the other agents:

```text
grounded deterministic output -> LLM refinement -> schema-validated response
```

The LLM receives:

- intent summary;
- context summary;
- discovered relationships;
- candidate federated views;
- current top view;
- federation plan;
- governance metadata.

The LLM returns strict JSON with:

- `recommended_view_id`;
- `overall_confidence`;
- `reasoning`;
- `governance_notes`;
- `plan_notes`.

The agent only accepts a `recommended_view_id` that exists in the candidate catalog.

---

## Verified Behaviour

Smoke test query:

```text
show total spend for customer 101 on 2026-03-10 with shopping behavior
```

Verified output:

| Output | Value |
| --- | --- |
| `/api/pipeline/run` status | 200 |
| Pipeline stage | `consumer_ready` |
| Execution result present | Yes |
| Normalized records | 4 |
| IBM normalized records | 1 |
| Unisys normalized records | 3 |
| Federation consumed normalization output | Yes |
| Federated total spend | 2000.0 |
| Double-counting protected | Yes |
| Frontend TypeScript | Pass (`npx tsc --noEmit`) |

Note: `npm run build` may fail on Windows with an `esbuild spawn EPERM` issue in this
environment, but TypeScript validation passed.
