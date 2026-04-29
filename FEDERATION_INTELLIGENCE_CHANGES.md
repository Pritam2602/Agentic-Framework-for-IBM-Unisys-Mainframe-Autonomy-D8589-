# Federation Intelligence Layer — Changes & Achievements

## What Was Built

A fully working **Federation Intelligence Layer** that slots between the Normalization Layer
and the Consumer Layer in the COMMUNICATOR stack. It identifies cross-system entity
relationships, scores and ranks federated business views against the current user intent,
generates a structured federation execution plan, executes the chosen view to return real
federated data, and records lineage and governance metadata for every field.

---

## Files Created

### `federation_intelligence/__init__.py`
Package entry point. Exports `run_federation_intelligence` (the agent's main function)
and `FederationIntelligenceOutput` so callers need only one import.

### `federation_intelligence/schemas.py`
Pydantic v2 models defining the layer's contract:

| Model | Purpose |
|-------|---------|
| `EntityRelationship` | One cross-system entity link (source/target entity, system, join key, relationship type, confidence, reasoning) |
| `FederatedView` | One candidate business view — its entities, IBM fields, Unisys fields, business value, applicability score, and recommendation reason |
| `FederationPlan` | How to execute: join strategy, financial-authority rule, enrichment fields, 8-step execution sequence, double-counting guard |
| `LineageRecord` | Per-field data lineage — which system and entity each output field comes from |
| `FederationIntelligenceOutput` | Full layer output combining all of the above plus federated data, governance metadata, confidence, and reasoning |
| `FederationAnalyzeRequest` | POST /api/federation/analyze request body |
| `FederationExecuteRequest` | POST /api/federation/execute request body |

### `federation_intelligence/entity_graph.py`
Builds a relationship graph across IBM and Unisys entities.

- Maintains a **relationship catalog** of 3 pre-defined cross-system links
  (transaction→shopping, account→shopping, customer→shopping) with confidence scores
  and reasoning derived from `mock_eportal/entity_mapping.json`.
- `build_entity_graph(intent_entities)` — returns all relationships relevant to the
  entities in the current intent.
- `_infer_relationships()` — fallback inference when entities are not in the catalog,
  using system-ownership rules to guess plausible join keys.
- `resolve_join_key()` — picks the most common join key across all discovered relationships.

### `federation_intelligence/view_recommender.py`
Scores and ranks the federated view catalog against the current intent.

**Catalog of 5 federated business views:**

| view_id | Business question answered |
|---------|---------------------------|
| `customer_spend_enriched` | 360° spend view — IBM amounts + all Unisys behavioral context |
| `merchant_category_spend` | Where does the customer spend by merchant and category? |
| `loyalty_spend_correlation` | How much loyalty value is earned per dollar spent? |
| `cart_conversion_analysis` | How do cart decisions translate to IBM-confirmed spend? |
| `browsing_to_spend_funnel` | Does longer browsing drive higher spend? |

Scoring weighs: entity overlap (35 %), metric match (25 %), task type (20 %),
federation flag (15 %), dual-system presence (5 %).

### `federation_intelligence/executor.py`
Executes any of the 5 federated views for a given `customerId` (and optional date)
by calling the existing functions in `app/federation/shopping_federation.py`.
Each view returns a structured dict with IBM financial data, Unisys enrichment,
and explicit notes preventing double-counting.

### `federation_intelligence/agent.py`
The main orchestrator — `run(intent, context, execute)`:

1. Extract intent entities and `requires_federation` flag.
2. Call `entity_graph.build_entity_graph()` to discover relationships.
3. Call `view_recommender.recommend_views()` to rank all 5 views.
4. Select the top-scoring view.
5. Call `_build_federation_plan()` to produce the 8-step execution plan.
6. Build field-level lineage (11 fields: 5 IBM, 6 Unisys).
7. If `execute=True` and a `customerId` filter is present, call `executor.execute_view()`.
8. Compute overall confidence from relationship confidence (40 %), context confidence (35 %),
   and view applicability (25 %).
9. Build governance metadata (timestamp, sources, double-counting protection flag, etc.).
10. Return `FederationIntelligenceOutput`.

---

## Files Modified

### `app/api/federation_intelligence.py` *(new)*
Four REST endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/federation/analyze` | Full Federation Intelligence: intent + context in, complete output out |
| `POST` | `/api/federation/execute` | Direct federated view execution by customerId and view_id |
| `GET` | `/api/federation/views` | Catalog of all 5 available federated views |
| `GET` | `/api/federation/health` | Health check with capability list |

### `app/api/pipeline.py`
Added **Step 3: Federation Intelligence** to the `/api/pipeline/run` endpoint.
The pipeline now runs: Intent Agent → Context Resolution Agent → Federation Intelligence.
`PipelineResponse` gained a `federation_intelligence` field.
The summary line now includes relationship count, top view name, and federation confidence.
`/api/pipeline/health` now reports `federation_intelligence: ready`.

### `app/main.py`
- Imported and registered `federation_router` (`/api/federation/*`).
- Added `/api/federation/analyze` and `/api/federation/views` to the root endpoint's
  `endpoints` map.
- Added `"federation_intelligence": "ready"` to the `/health` response.

---

## What the Layer Achieves

### Entity Relationship Discovery
Given any user intent, the layer identifies every meaningful cross-system relationship
between IBM and Unisys entities. Each relationship includes its join key, type
(enrichment / reconciliation / reference / mirror), confidence score, and a plain-English
reasoning string derived from the live entity mapping catalog.

### Federated View Recommendation
The layer scores all 5 business views against the current intent and returns them in
ranked order. Each view specifies exactly which IBM fields (financial truth) and Unisys
fields (behavioral enrichment) are combined, along with the business value and a
recommendation reason tailored to the intent.

### Federation Plan Generation
A structured, 8-step execution plan is produced for every request. It names the primary
source (IBM), the enrichment source (Unisys), the join strategy (left join on customerId),
and includes an explicit double-counting guard preventing Unisys amounts from being added
to IBM amounts.

### Federation Execution
When a `customerId` filter is present in the intent, the layer executes the top-ranked
view and returns real federated data: IBM spend totals, transaction counts, and full
Unisys behavioral enrichment (category breakdown, merchant insights, loyalty summary,
browsing metrics, cart analysis).

### Data Lineage
Every output field is tagged with its source system, source entity, and any
transformation applied — 11 fields across 5 IBM + 6 Unisys columns.

### Governance Metadata
Each response carries: audit timestamp (UTC), sources accessed, join key used,
financial authority declaration, enrichment authority declaration, double-counting
protection flag, execution flag, overall confidence score, relationship count, and
views evaluated count.

### Pipeline Integration
The full `/api/pipeline/run` endpoint now delivers all three layers in one call:
intent understanding, context resolution, and federation intelligence — with a unified
summary string covering all three stages.

---

## Verified Behaviour (smoke test)

Input: analyze intent on `[transaction, shopping]` for `total_spend`, customer 101, date 2026-03-10.

| Output | Value |
|--------|-------|
| Entity relationships discovered | 3 |
| Views ranked | 5 (all views) |
| Top view | `customer_spend_enriched` (score 1.0) |
| Federation plan steps | 8 |
| Lineage fields tracked | 11 |
| IBM total spend (customer 101, 2026-03-10) | $2,000.00 |
| IBM transaction count | 1 |
| Top spending category (Unisys) | electronics |
| Overall confidence | 91.1 % |
| Double-counting protected | Yes |
