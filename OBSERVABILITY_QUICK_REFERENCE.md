# COMMUNICATOR - Observability Quick Reference

## System at a Glance

```
User Query
   ↓ (Intent Agent - WHAT)
Entities + Task + Filters
   ↓ (Context Resolution - WHERE)
IBM Programs & Unisys APIs
   ↓ (Planner - HOW)
Execution DAG with Steps
   ↓ (Execution Agent - RUN)
Step Results
   ↓ (Normalization - CANONICAL)
Normalized Records
   ↓ (Federation Intelligence)
Federated View Recommendation
```

---

## Key Metrics to Monitor (By Priority)

### CRITICAL - Monitor Every Request
```
✓ pipeline_total_end_to_end_ms          ← Should be < 3000ms
✓ pipeline_failure_rate                 ← Should be 0%
✓ amount_authority_violations_total     ← Should be 0 (financial integrity)
✓ join_key_mismatch_rate               ← Should be < 1%
```

### HIGH - Monitor Per Stage
```
✓ intent_agent_parse_time_ms            ← Should be < 500ms
✓ context_resolution_time_ms            ← Should be < 1500ms
✓ planner_time_ms                       ← Should be < 1000ms
✓ execution_time_ms                     ← Should be < 500ms
✓ normalization_time_ms                 ← Should be < 200ms
✓ federation_time_ms                    ← Should be < 200ms
```

### HIGH - Quality Metrics
```
✓ intent_agent_confidence_score         ← Should be > 0.85
✓ context_resolution_confidence         ← Should be > 0.80
✓ federation_confidence_score           ← Should be > 0.85
```

### MEDIUM - Error Tracking
```
✓ llm_fallback_total                    ← Should be < 5% of requests
✓ execution_errors_total                ← Track by error type
✓ schema_violations_total               ← Should be 0
✓ governance_violations_total           ← Should be 0
```

### MEDIUM - Data Quality
```
✓ records_processed_by_stage            ← Track data loss
✓ records_dropped_in_normalization      ← Should be < 5%
✓ entity_relationships_discovered       ← Should be > 1 for federated queries
```

---

## Trace Points - Add These First

### In `app/main.py` (FastAPI Setup)
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# After creating app
FastAPIInstrumentor.instrument_app(app)
```

### In `app/api/pipeline.py` (Pipeline Entry)
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@router.post("/run")
async def run_pipeline(request: PipelineRequest):
    with tracer.start_as_current_span("pipeline.execute") as span:
        span.set_attribute("query", request.user_query)
        # ... rest of pipeline code
        span.set_attribute("status", "success")
        return response
```

### In Each Agent's `run()` Method
```python
def run(self, ...):
    with tracer.start_as_current_span(f"{agent_name}.run") as span:
        start = time.time()
        # ... agent logic
        span.set_attribute("status", "success")
        span.set_attribute("duration_ms", (time.time() - start) * 1000)
        return result
```

---

## Critical Observability Rules

### ⚠️ MUST TRACK - Financial Data
- **Amount Authority Violations**: IBM is truth, Unisys is enrichment
- **Join Key Matching**: customerId must match between systems
- **Deduplication**: Never sum IBM + Unisys amounts

### ⚠️ MUST TRACK - System State
- **LLM Failures**: Track when fallback is used (should be rare)
- **Entity Resolution**: What entities were found vs requested
- **Governance Checks**: All governance rules enforcement

### ⚠️ MUST TRACK - Data Quality
- **Schema Violations**: Track what fields are missing/invalid
- **Records Dropped**: How much data is lost in each stage
- **Transformation Accuracy**: Are field mappings working

### ⚠️ MUST TRACK - Cross-System Federation
- **Join Success Rate**: How often customerId matches
- **Relationship Count**: How many entity relationships found
- **Federation Confidence**: Is the view recommendation confident

---

## Instrumentation Checklist

- [ ] **Week 1**: FastAPI middleware + basic tracing
- [ ] **Week 1**: Prometheus metrics setup
- [ ] **Week 2**: Instrument all 6 agent stages
- [ ] **Week 2**: Add domain-specific metrics
- [ ] **Week 3**: Add structured logging (JSON)
- [ ] **Week 3**: Create Grafana dashboards
- [ ] **Week 4**: Set up Prometheus alerts
- [ ] **Week 4**: Document SLA targets

---

## Log Message Examples

```python
# Intent Agent
logger.info("Intent parsed", extra={
    "request_id": "req-123",
    "entities": ["shopping"],
    "task": "fetch",
    "confidence": 0.92,
    "fallback": False
})

# Context Resolution
logger.info("Context resolved", extra={
    "request_id": "req-123",
    "ibm_program": "CARDEMO",
    "unisys_api": "/api/shopping",
    "ibm_confidence": 0.95,
    "unisys_confidence": 0.90,
    "total_confidence": 0.93
})

# Execution
logger.info("Execution completed", extra={
    "request_id": "req-123",
    "steps_executed": 2,
    "ibm_records": 125,
    "unisys_records": 89,
    "errors": 0,
    "duration_ms": 567
})

# Critical: Amount Authority
logger.warning("Amount authority check", extra={
    "request_id": "req-123",
    "ibm_amount_total": 1500.00,
    "unisys_amount_total": 1450.00,
    "mismatch": 50.00,
    "action": "using_ibm_as_truth"
})

# Critical: Join Key Mismatch
logger.error("Join key failure", extra={
    "request_id": "req-123",
    "customer_id_ibm": 101,
    "customer_id_unisys": 102,
    "severity": "critical",
    "action": "federation_aborted"
})
```

---

## Grafana Dashboard Panels

Create a dashboard with these sections:

### Section 1: Pipeline Health
- Total latency (gauge)
- Success rate (gauge)
- Error rate (graph)
- Status by stage (table)

### Section 2: Stage Breakdown
- Intent parse time (histogram)
- Context resolution time (histogram)
- Planner time (histogram)
- Execution time (histogram)
- Normalization time (histogram)
- Federation time (histogram)

### Section 3: Quality Metrics
- Intent confidence (gauge)
- Context confidence (gauge)
- Federation confidence (gauge)
- Entity relationships found (stat)

### Section 4: Error Tracking
- Execution errors by stage (bar chart)
- Amount authority violations (counter)
- Join key mismatches (counter)
- Schema violations (counter)
- LLM fallback rate (graph)

### Section 5: Data Flow
- Records input/output by stage (stacked bar)
- Data loss percentage (gauge)
- Federated queries success (stat)

### Section 6: System Resources
- LLM tokens used (counter)
- LLM cost (stat)
- Average requests/min (graph)

---

## Alerting Rules

```yaml
CRITICAL (Page On-Call):
  - pipeline_failed: Any request fails
  - amount_authority_violation: Financial rule broken
  - join_key_mismatch_rate > 5%: Data integrity issue

SEVERE (Create Incident):
  - latency > 3000ms for > 5 consecutive requests
  - error_rate > 1% for > 10m
  - llm_fallback_rate > 10%
  - federation_confidence < 0.5

WARNING (Create Ticket):
  - latency > 2000ms for > 15m
  - error_rate > 0.1% for > 30m
  - any schema violation
  - entity_relationships < 1 for federated query
```

---

## Sample Query Telemetry

### Example Request: "Show me shopping data for customer 101"

```
Request ID: req-abc123
Timeline:
├─ Middleware [1ms] - request received
├─ Intent Agent [145ms]
│  ├─ LLM Call [125ms] - parsed 1 entity, 1 filter
│  ├─ Confidence [0.95]
│  └─ Fallback [No]
├─ Context Resolution [234ms]
│  ├─ IBM Lookup [98ms] - found CARDEMO program
│  ├─ Unisys Lookup [136ms] - found /api/shopping endpoint
│  └─ Confidence [0.92]
├─ Planner [267ms]
│  ├─ DAG Build [45ms] - 2 steps created
│  ├─ LLM Refinement [180ms]
│  └─ Risk Assessment [42ms] - all LOW
├─ Execution [412ms]
│  ├─ IBM Step 1 [201ms] - 125 records
│  ├─ Unisys Step 2 [211ms] - 89 records
│  └─ Total Records [214]
├─ Normalization [98ms]
│  ├─ Field Mapping [45ms]
│  ├─ Validation [23ms] - 0 violations
│  ├─ Amount Authority Check [20ms] - OK
│  └─ Output Records [214]
└─ Federation [156ms]
   ├─ Discovery [45ms]
   ├─ Entity Graph [56ms]
   ├─ Join Resolution [35ms] - 214 matches
   └─ View Recommended [federation_shopping_v1] at confidence [0.91]

METRICS:
- Total latency: 1,313ms ✓ (< 3000ms)
- Intent confidence: 0.95 ✓ (> 0.85)
- Context confidence: 0.92 ✓ (> 0.80)
- Federation confidence: 0.91 ✓ (> 0.85)
- Join success rate: 100% ✓ (214/214)
- Records retained: 100% ✓ (0 dropped)
- Amount authority: OK ✓ (IBM as truth)
- Errors: 0 ✓
- Status: SUCCESS ✓
```

---

## Performance Targets (SLAs)

| Metric | Target | Critical |
|--------|--------|----------|
| Total Pipeline Latency | < 2000ms | > 3000ms |
| Intent Parsing | < 500ms | > 1000ms |
| Context Resolution | < 1500ms | > 2000ms |
| Execution | < 500ms | > 1500ms |
| Pipeline Success Rate | > 99% | < 95% |
| Intent Confidence | > 0.85 | < 0.60 |
| Federation Confidence | > 0.85 | < 0.50 |
| LLM Fallback Rate | < 5% | > 20% |
| Join Key Match Rate | > 99% | < 90% |
| Amount Authority Violations | 0 | > 0 |
| Schema Violations | 0 | > 5/hour |

---

## Troubleshooting Guide

### If latency is high:
- Check which stage is slow
- If Intent Agent: LLM may be slow, check model
- If Context Resolution: Catalog lookups may be slow
- If Execution: Check underlying system performance

### If confidence is low:
- Check entity resolution
- Check filter extraction accuracy
- May indicate ambiguous query

### If join keys mismatch:
- Check if systems have consistent customer IDs
- May indicate data quality issue
- Review federation_intelligence logs

### If amount authority violation:
- **CRITICAL**: Check why IBM and Unisys amounts differ
- May indicate missing data or transformation error
- Escalate immediately

### If LLM fallback is high:
- LLM may be down or failing
- Check LLM model availability
- Rule-based fallback should be good enough

---

## Quick Start Implementation

```python
# Step 1: Install dependencies
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger \
            opentelemetry-exporter-prometheus opentelemetry-instrumentation-fastapi \
            prometheus-client

# Step 2: In app/main.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Step 3: In each agent
from opentelemetry import trace
tracer = trace.get_tracer(__name__)

# Step 4: Wrap agent runs
with tracer.start_as_current_span("agent.name") as span:
    result = agent.run(...)
    span.set_attribute("status", "success")

# Step 5: Run observability stack
docker-compose up -d jaeger prometheus grafana

# Step 6: Access dashboards
# Jaeger: http://localhost:16686
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

---

## Resources

- OpenTelemetry Docs: https://opentelemetry.io/
- Jaeger Documentation: https://www.jaegertracing.io/
- Prometheus Docs: https://prometheus.io/
- Grafana Docs: https://grafana.com/docs/

