# COMMUNICATOR Observability Strategy - Executive Summary

## Overview

This observability strategy provides complete visibility into the **COMMUNICATOR** data federation platform's complex multi-agent pipeline. The system orchestrates 6 specialized AI agents to federate IBM mainframe and Unisys data.

---

## What is COMMUNICATOR?

**COMMUNICATOR** is an AI-driven data federation platform with this pipeline:

```
User Natural Language Query
        ↓
[1] Intent Agent         - Understands WHAT user wants
        ↓
[2] Context Agent        - Resolves WHERE data exists  
        ↓
[3] Planner Agent        - Creates HOW to fetch data
        ↓
[4] Execution Agent      - Runs the plan
        ↓
[5] Normalization Agent  - Maps to common schema
        ↓
[6] Federation Agent     - Discovers relationships
        ↓
Federated View Result
```

Each stage adds intelligence and safety checks. **Observability must track all of them.**

---

## Why Observability Matters Here

### 1. **Complex Pipeline**
- 6 independent agents in sequence
- Each has LLM + deterministic fallback
- Failures can occur at any stage
- **Need**: End-to-end tracing to find bottlenecks

### 2. **LLM-Based Intelligence**
- Models parse intent, suggest refinements
- Fallback to rule-based if LLM fails
- Token usage = operational cost
- **Need**: Track model performance and costs

### 3. **Cross-System Federation**
- Reconciling IBM mainframe + Unisys data
- Join keys must match exactly
- Financial amounts have authority rules
- **Need**: Monitor federation accuracy and conflicts

### 4. **Financial Data Handling**
- IBM amounts are TRUTH
- Unisys amounts are enrichment only
- Never sum them together
- **Need**: Detect and alert on authority violations

### 5. **Data Quality & Governance**
- Schema validations at each stage
- Governance rules enforcement
- Audit trails required
- **Need**: Track all transformations and rule checks

---

## Architecture Overview

### The Complete Data Flow

```
USER QUERY (string)
    │ "Show shopping data for customer 101"
    ├─ Word count, length, language
    │
    ▼
[1] INTENT AGENT
    │ Extracts: entities, task, filters, metrics
    ├─ LLM: "What does user want?" (0.1 - 0.5s)
    ├─ Fallback: Rule-based extraction
    ├─ Confidence score (0-1)
    │ Output: IntentOutput
    │ { entities: ["shopping"], task: "fetch", filters: {...} }
    │
    ▼
[2] CONTEXT RESOLUTION AGENT
    │ Maps entities to systems
    ├─ IBM path: Look up programs, datasets, JCL
    ├─ Unisys path: Look up APIs, fields, tools
    ├─ Confidence score (0-1)
    │ Output: ContextOutput
    │ { ibm: {...}, unisys: {...} }
    │
    ▼
[3] PLANNER AGENT
    │ Creates execution plan with dependencies
    ├─ Build DAG of steps
    ├─ Assess risk levels
    ├─ Select safe commands
    ├─ LLM: Refine strategy (optional)
    │ Output: PlannerOutput
    │ { steps: [{id, system, action, risk, dependencies}] }
    │
    ▼
[4] EXECUTION AGENT
    │ Routes to appropriate executors
    ├─ IBM: JobExecutor, DatasetExecutor, WorkflowExecutor
    ├─ Unisys: Mock ePortal services
    ├─ Mode: safe_mock by default
    │ Output: ExecutionResult
    │ { step_results: [{status, records}] }
    │
    ▼
[5] NORMALIZATION AGENT
    │ Maps to canonical schema
    ├─ Field alignment (IBM ↔ Unisys)
    ├─ CRITICAL: Amount authority check
    │   - IBM is truth
    │   - Unisys is enrichment
    │   - NEVER sum them
    ├─ Schema validation
    │ Output: NormalizedRecords
    │ { records: [{customerId, amount, date, ...}] }
    │
    ▼
[6] FEDERATION INTELLIGENCE
    │ Discovers entity relationships
    ├─ Build entity graph
    ├─ Resolve join keys
    ├─ Generate view recommendations
    ├─ Calculate confidence
    │ Output: FederatedView
    │ { name, entities, relationships, confidence: 0.91 }
    │
    ▼
FINAL RESPONSE
```

---

## Critical Observability Points

### ⚠️ HIGHEST PRIORITY: Financial Data Integrity

```
Amount Authority Rule: IBM is TRUTH, Unisys is ENRICHMENT
                         ↓
    Track every place amounts are handled:
    ├─ Execution Agent fetches amounts
    ├─ Normalization Agent validates amounts
    ├─ Federation Intelligence compares amounts
    └─ ANY violation → ALERT IMMEDIATELY
    
Metrics to Track:
✓ amount_authority_violations_total    (should be 0)
✓ amount_mismatch_detected              (alert on any)
✓ ibm_amount_total vs unisys_amount_total (compare)
✓ deduplication_applied_count           (track rule enforcement)
```

### ⚠️ CRITICAL: Cross-System Join Keys

```
Join Key: customerId must match between systems
            ↓
    Track join success at Federation stage:
    ├─ Total records to join
    ├─ Successful joins (customerId matched)
    ├─ Failed joins (customerId mismatched)
    └─ Join success rate (should be > 99%)
    
Metrics to Track:
✓ join_attempts_total
✓ join_successes_total
✓ join_failures_total
✓ join_key_mismatch_rate        (alert if > 1%)
```

### ⚠️ HIGH: LLM Reliability

```
LLM Usage in Agents:
├─ Intent Agent: Parse query (may fail)
├─ Planner Agent: Refine strategy (optional)
├─ Normalization Agent: Explain mapping (optional)
├─ Federation Agent: Recommend view (optional)
    ↓
    Track LLM vs Fallback:
    ├─ How many requests used LLM?
    ├─ How many fell back to rules?
    ├─ What was error rate?
    └─ Fallback should work most of time
    
Metrics to Track:
✓ llm_calls_total
✓ llm_fallback_total            (alert if > 5%)
✓ llm_success_rate
✓ llm_error_rate
✓ llm_tokens_used_total         (cost tracking)
```

### ⚠️ HIGH: Pipeline Performance

```
Latency Budget (Target: < 2000ms end-to-end):
├─ Intent Agent: 500ms max
├─ Context Resolution: 1500ms max
├─ Planner: 1000ms max
├─ Execution: 500ms max
├─ Normalization: 200ms max
└─ Federation: 200ms max
    ↓
    Track each stage:
    ├─ Are we within budget?
    ├─ Which stage is slow?
    └─ Any trends toward slowness?
    
Metrics to Track:
✓ pipeline_total_end_to_end_ms  (alert if > 3000ms)
✓ intent_agent_parse_time_ms
✓ context_resolution_time_ms
✓ planner_time_ms
✓ execution_time_ms
✓ normalization_time_ms
✓ federation_time_ms
```

### ⚠️ MEDIUM: Data Quality

```
Data Flow Tracking:
Record 1 → Stage 1 → Stage 2 → ... → Final
    ↓
    Track at each stage:
    ├─ Records input
    ├─ Records output
    ├─ Records dropped
    ├─ Why dropped?
    └─ Schema violations?
    
Metrics to Track:
✓ records_processed_by_stage
✓ records_dropped_in_stage      (track %lost)
✓ schema_violations_total       (alert if > 0)
✓ transformation_errors_total
```

### 🟡 MEDIUM: Confidence Scores

```
Each Stage Produces Confidence (0-1):
├─ Intent confidence: How sure about entity/task?
├─ Context confidence: How sure about data location?
├─ Federation confidence: How sure about relationships?
    ↓
    Low confidence may mean:
    ├─ Query is ambiguous
    ├─ Systems don't have data
    ├─ Join keys don't match
    └─ Need human review
    
Metrics to Track:
✓ intent_confidence_score       (alert if < 0.60)
✓ context_confidence_score      (alert if < 0.60)
✓ federation_confidence_score   (alert if < 0.60)
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
**Goal**: Basic tracing & metrics infrastructure

```
Tasks:
☐ Install OpenTelemetry + Jaeger + Prometheus + Grafana
☐ Add FastAPI instrumentation to app/main.py
☐ Add middleware for request ID correlation
☐ Set up Prometheus metric collection
☐ Verify traces show up in Jaeger UI

Deliverables:
✓ All requests have trace IDs
✓ Prometheus scraping metrics
✓ Jaeger receiving spans
```

### Phase 2: Agent Instrumentation (Week 3-4)
**Goal**: Detailed tracing of each agent stage

```
Tasks:
☐ Instrument Intent Agent (parse time, confidence, LLM calls)
☐ Instrument Context Resolution (lookup times, confidence)
☐ Instrument Planner (DAG creation, risk assessment)
☐ Instrument Execution (step routing, execution times)
☐ Instrument Normalization (schema violations, amount checks)
☐ Instrument Federation (entity discovery, join success)

Deliverables:
✓ Each stage shows in Jaeger trace
✓ Timing breakdown visible
✓ Decision points logged
```

### Phase 3: Domain Metrics (Week 5-6)
**Goal**: Business-level KPIs and data quality metrics

```
Tasks:
☐ Add amount authority violation tracking
☐ Add join key success rate tracking
☐ Add federation confidence metrics
☐ Add records flow metrics (input/output/dropped per stage)
☐ Add governance rule check tracking
☐ Add LLM token usage tracking

Deliverables:
✓ Financial integrity metrics
✓ Data quality metrics
✓ Federation success metrics
```

### Phase 4: Dashboards & Alerts (Week 7-8)
**Goal**: Visualization & automated alerting

```
Tasks:
☐ Create Grafana dashboard: Pipeline Health
☐ Create Grafana dashboard: Stage Breakdown
☐ Create Grafana dashboard: Data Quality
☐ Create Grafana dashboard: Financial Integrity
☐ Set up Prometheus alerts (critical, severe, warning)
☐ Configure alert routing (PagerDuty/Slack)
☐ Document alert runbooks

Deliverables:
✓ Real-time dashboards
✓ Automated alerts
✓ Runbook for each alert
```

---

## Key Metrics Summary

### Must-Have Metrics (Instrument First)
```
✓ pipeline_total_end_to_end_ms
✓ pipeline_failure_rate
✓ intent_agent_parse_time_ms
✓ context_resolution_time_ms
✓ execution_errors_total
✓ amount_authority_violations_total
✓ join_key_mismatch_rate
```

### Should-Have Metrics (High Value)
```
✓ intent_confidence_score
✓ context_confidence_score
✓ federation_confidence_score
✓ llm_fallback_rate
✓ records_dropped_by_stage
✓ llm_tokens_used_total
✓ entity_relationships_discovered
```

### Nice-to-Have Metrics (Future)
```
✓ Detailed field mapping accuracy
✓ Governance rule compliance percentage
✓ LLM cost tracking
✓ Cache hit rates
✓ User satisfaction scores
```

---

## Documents in This Repository

1. **ARCHITECTURE_AND_OBSERVABILITY_ANALYSIS.md** (This one)
   - Complete system architecture
   - Data flow at each stage
   - Observability requirements
   - Implementation strategy

2. **OBSERVABILITY_INSTRUMENTATION_GUIDE.md**
   - Detailed code examples
   - Instrumentation patterns
   - Metrics definitions
   - Alert rules
   - Grafana dashboard JSON

3. **OBSERVABILITY_QUICK_REFERENCE.md**
   - Quick lookup guide
   - Key metrics list
   - SLA targets
   - Troubleshooting guide
   - Sample telemetry

---

## Next Steps

1. **Review** this document and understand the pipeline
2. **Schedule** observability implementation sprints
3. **Assign** team members to phases
4. **Set up** infrastructure (Jaeger, Prometheus, Grafana)
5. **Implement** instrumentation following guides
6. **Create** dashboards and alerts
7. **Monitor** and iterate

---

## Success Criteria

By end of Phase 4, we should have:

- ✅ **Complete visibility** into all 6 agent stages
- ✅ **Latency tracking** with < 2000ms target
- ✅ **Quality metrics** showing data integrity
- ✅ **Financial integrity** with 0 authority violations
- ✅ **Federation success** with > 85% confidence
- ✅ **Automated alerts** for critical issues
- ✅ **Real-time dashboards** for operators
- ✅ **Cost visibility** for LLM token usage

---

## Contact & Support

For questions on observability implementation:
- Review the detailed guides above
- Refer to OpenTelemetry/Jaeger/Prometheus documentation
- Check tool-specific troubleshooting sections

---

## Appendix: Glossary

**Intent**: What the user wants (entities, task, filters)
**Context**: Where the data exists (systems, programs, APIs)
**Plan**: How to fetch the data (execution steps with dependencies)
**Execution**: Running the plan (fetching actual data)
**Normalization**: Converting to common schema
**Federation**: Discovering relationships between entities
**Confidence**: How confident is the system (0-1 score)
**Fallback**: Rule-based alternative when LLM fails
**Amount Authority**: Financial truth rule (IBM > Unisys)
**Join Key**: Field used to match records across systems (customerId)
**Trace**: Complete request path through all stages
**Span**: Individual operation within a trace

