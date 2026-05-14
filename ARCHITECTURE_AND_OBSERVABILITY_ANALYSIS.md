# Data Federation Framework - Architecture & Observability Analysis

## Executive Summary

The **COMMUNICATOR** platform is an AI-driven data federation system that orchestrates multi-agent workflows to integrate IBM mainframe and Unisys systems. The system has 6 core agent stages, each transforming data progressively from natural language to executable federated views.

**Critical Insight**: This is a complex LLM-orchestrated pipeline with deterministic validation layers. Observability must track:
- Agent latency and decision quality
- LLM token usage and cost
- Data transformation accuracy
- Cross-system federation success rates
- Governance rule compliance

---

## 1. DATA FLOW ARCHITECTURE

### The Complete Pipeline Flow

```
USER QUERY (string)
    ↓
[1] INTENT AGENT (Parse WHAT)
    ↓ (IntentOutput: entities, task, filters, metrics)
[2] CONTEXT RESOLUTION AGENT (Resolve WHERE)
    ↓ (ContextOutput: IBM programs/datasets, Unisys APIs)
[3] PLANNER AGENT (Create HOW plan)
    ↓ (PlannerOutput: DAG of execution steps)
[4] EXECUTION AGENT (Validate & Execute)
    ↓ (ExecutionResult: step outputs, errors)
[5] NORMALIZATION AGENT (Map to canonical)
    ↓ (NormalizedRecords: consistent schema)
[6] FEDERATION INTELLIGENCE (Discover relations)
    ↓
FEDERATED VIEW (final output)
```

---

## 2. DETAILED STAGE BREAKDOWN

### Stage 1: Intent Agent
**Location**: `intent_agent/agent.py`
**Input**: User natural language query
**Output**: `IntentOutput` with:
- `entities` (business objects: shopping, transaction, account)
- `task` (fetch, analyze, compare, discover, reconcile)
- `filters` (field-value conditions)
- `metric` (total_spend, average_spend, etc.)
- `aggregation` (sum, avg, count)
- `output_mode` (list, aggregate, detailed)
- `confidence_score` (0-1)

**Key Logic**:
```
Entity Priority: shopping > transaction > account > customer
System Mapping:
  - shopping → Unisys
  - transaction → IBM
  - inventory → Unisys
  - account → IBM
```

**Fallback**: LLM → Rule-based extractor (if LLM fails)

**Critical Rules**:
- Entities are BUSINESS OBJECTS (not identifiers)
- Filters are conditions (customerId, date ranges)
- "customer 101" → entity=shopping, filter={customerId: 101}

---

### Stage 2: Context Resolution Agent
**Location**: `context_resolution_agent/agent.py`
**Input**: IntentOutput
**Output**: `ContextOutput` with IBM and Unisys resolved metadata

#### IBM Resolution
Maps to:
- `program` (COBOL program ID from CardDemo)
- `jcl_job` (JCL job that runs the program)
- `primary_dataset` (main data source)
- `all_datasets` (related datasets)
- `key_variables` (COBOL variables involved)

#### Unisys Resolution
Maps to:
- `api_endpoint` (REST API path)
- `fields` (response fields)
- `tool_name` (MCP tool)
- `params` (query parameters)

**Confidence Score**: Based on metadata availability (0-1)

---

### Stage 3: Planner Agent
**Location**: `planner_agent/agent.py`
**Input**: Intent + Context
**Output**: `PlannerOutput` with DAG execution plan

**Creates**:
- Execution steps with dependencies
- Risk levels (LOW, MEDIUM, HIGH, CRITICAL)
- Command selections from allowlist
- Governance controls

**LLM Role**: Optional refinement only (cannot invent commands)

**Guarantees**:
- IBM CardDemo amounts are FINANCIAL TRUTH
- Unisys data is BEHAVIORAL ENRICHMENT only
- Never sums IBM + Unisys amounts

---

### Stage 4: Execution Agent
**Location**: `execution_agent/agent.py`
**Input**: Planner output
**Output**: `ExecutionResult` with execution trace

**Routes To**:
- `JobExecutor` (JCL jobs)
- `DatasetExecutor` (Dataset operations)
- `WorkflowExecutor` (Mainframe workflows)
- `MockZOSSimulator` (Mock mainframe)
- `ShoppingService` (Unisys mock)
- `InventoryService` (Unisys mock)

**Safety**: All real execution is "safe_mock" mode by default

---

### Stage 5: Normalization Agent
**Location**: `normalization_agent/agent.py`
**Input**: Execution results
**Output**: `NormalizedRecords` with canonical schema

**Performs**:
- Field mapping (IBM → Unisys field alignment)
- Amount deduplication (IBM is truth)
- Schema validation
- Warning generation for data quality

**Domain Rules**:
- `customerId` is primary join key
- `amount` from IBM is authoritative
- Unisys amounts are enrichment only

---

### Stage 6: Federation Intelligence
**Location**: `federation_intelligence/agent.py`
**Input**: Normalized output + metadata
**Output**: Recommended federated view

**Components**:
1. **Discovery** (`discovery.py`): Find capabilities
2. **Entity Graph** (`entity_graph.py`): Build relationships
3. **View Recommender** (`view_recommender.py`): Select best view
4. **Executor** (`executor.py`): Execute view
5. **Recommendations** (`recommendations.py`): Related entities

**Outputs**:
- Entity relationships
- Lineage records
- Governance metadata
- Confidence scores

---

## 3. DATA TRANSFORMATIONS BY STAGE

### Intent Agent
```
"Show me shopping data for customer 101 on 2026-03-10"
        ↓
{
  "entities": ["shopping"],
  "task": "fetch",
  "filters": {
    "conditions": [
      {"field": "customerId", "value": 101},
      {"field": "date", "value": "2026-03-10"}
    ]
  },
  "confidence_score": 0.95
}
```

### Context Agent
```
IntentOutput
        ↓
{
  "ibm": {
    "program": "CARDEMO",
    "jcl_job": "CARDTX",
    "primary_dataset": "CARDEMO.TRANSACTIONS"
  },
  "unisys": {
    "api_endpoint": "/api/unisys/shopping",
    "fields": ["merchant", "category", "amount"],
    "tool_name": "shopping_api"
  },
  "resolution_confidence": 0.90
}
```

### Planner Agent
```
ContextOutput
        ↓
{
  "status": "valid",
  "plan": {
    "steps": [
      {
        "order": 1,
        "system": "ibm",
        "step_type": "ibm_dataset",
        "command": "zowe zos-files list data-set"
      },
      {
        "order": 2,
        "system": "unisys",
        "step_type": "unisys_api",
        "endpoint": "/api/unisys/shopping"
      }
    ]
  }
}
```

### Execution Agent
```
PlannerOutput
        ↓
{
  "status": "completed",
  "steps_executed": 2,
  "step_results": [
    {
      "step_id": "1",
      "status": "success",
      "records_returned": 125,
      "execution_time_ms": 234
    },
    {
      "step_id": "2",
      "status": "success",
      "records_returned": 89,
      "execution_time_ms": 156
    }
  ]
}
```

### Normalization Agent
```
ExecutionResult
        ↓
{
  "entity": "transaction",
  "total_records": 125,
  "canonical_records": [
    {
      "customerId": 101,
      "transactionId": "TXN-001",
      "amount": 150.00,
      "date": "2026-03-10",
      "source_system": "ibm"
    }
  ]
}
```

### Federation Intelligence
```
NormalizedRecords
        ↓
{
  "entity_relationships": [
    {
      "entity1": "transaction",
      "entity2": "shopping",
      "join_key": "customerId",
      "relationship_type": "federation"
    }
  ],
  "top_view": {
    "name": "customer_spending_analysis",
    "entities": ["transaction", "shopping"],
    "confidence": 0.92
  }
}
```

---

## 4. CRITICAL DECISION POINTS

### Where Intelligence Matters
1. **Intent Entity Priority** - Which entity is primary?
2. **System Ownership** - Which system owns this data?
3. **Join Key Selection** - How do IBM + Unisys connect?
4. **Amount Authority** - Which system is source of truth?
5. **Federation Confidence** - Can we safely federate?

### Where Safety Matters
1. **Never add IBM + Unisys amounts together**
2. **customerId must match exactly between systems**
3. **No destructive operations in safe_mock mode**
4. **Governance rules must be enforced**

---

## 5. OBSERVABILITY REQUIREMENTS

### 5.1 Metrics to Track

#### Latency Metrics
```
- intent_agent.parse_time_ms
- context_resolution.resolve_time_ms
- planner.plan_generation_time_ms
- execution.total_execution_time_ms
- normalization.normalization_time_ms
- federation_intelligence.discovery_time_ms
- pipeline.total_end_to_end_ms
```

#### Quality Metrics
```
- intent_agent.confidence_score (0-1)
- context_resolution.confidence_score (0-1)
- federation_intelligence.overall_confidence (0-1)
- entity_relationships.count
- successful_federations / total_attempts
- normalization_errors.count
```

#### System Metrics
```
- llm_model.tokens_used
- llm_model.tokens_cost
- llm_model.failures
- llm_model.fallback_usage (times rule-based fallback used)
- execution_errors.count
- execution_errors.by_type (by_system, by_step_type)
```

#### Data Metrics
```
- records_processed.by_stage
- records_dropped.by_stage
- data_transformation_accuracy
- schema_violations.count
- governance_rule_violations.count
```

#### Federation Metrics
```
- federation_success_rate
- join_key_matches / mismatches
- amount_authority_conflicts
- entity_relationship_density
```

### 5.2 Logging Points

#### Structured Logs
- Stage entry/exit with timing
- Decision points (entity choice, system selection)
- LLM calls (prompt, response, tokens, latency)
- Fallback activations
- Errors and warnings
- Governance rule checks

#### Trace Events
Each stage should emit TraceEvent objects with:
- `timestamp`
- `stage_name`
- `event_type`
- `data` (transformed data at that point)
- `duration_ms`
- `status` (success/warning/error)

### 5.3 Distributed Tracing
Track request ID through all stages:
```
Request ID: req-12345
├─ Intent Agent [25ms]
│  └─ LLM Call [20ms]
├─ Context Resolution [150ms]
│  ├─ IBM Resolution [75ms]
│  └─ Unisys Resolution [75ms]
├─ Planner [300ms]
│  └─ LLM Refinement [250ms]
├─ Execution [500ms]
│  ├─ Job Step 1 [200ms]
│  └─ API Step 2 [300ms]
├─ Normalization [100ms]
└─ Federation Intelligence [200ms]
TOTAL: 1,275ms
```

### 5.4 Alerting Points

**Critical**:
- Pipeline failure at any stage
- LLM fallback more than N times per hour
- Governance rule violation
- Amount mismatch (IBM vs Unisys)
- Join key failures

**Warning**:
- Latency exceeds SLA (e.g., >2000ms)
- Confidence score < 0.5
- Entity relationships < expected
- Data quality issues
- Schema violations

---

## 6. INSTRUMENTATION STRATEGY

### Where to Instrument

#### High Priority (Immediate)
```
1. Pipeline entry/exit (FastAPI middleware)
2. Each agent's run() method
3. LLM calls in agents
4. Critical decision points
5. Error handling
```

#### Medium Priority (Phase 2)
```
1. Data transformations by stage
2. Executor routing decisions
3. Federation relationship building
4. Governance rule checks
5. Mock service calls
```

#### Low Priority (Phase 3)
```
1. Fallback path activations
2. Rule-based extractor usage
3. Catalog lookups
4. Schema validation details
```

### Tool Stack Recommendations

#### Tracing
- **OpenTelemetry** + **Jaeger/DataDog** for distributed tracing
- Integrate with FastAPI via ASGI middleware
- Propagate trace context through LLM calls

#### Metrics
- **Prometheus** for metrics collection
- Custom metrics for domain-specific KPIs
- Histogram for latencies, Gauge for in-flight requests

#### Logging
- **Structured logging** (JSON) with correlation IDs
- **ELK Stack** or **Loki** for log aggregation
- Consistent log format across all agents

#### Dashboarding
- **Grafana** for real-time visualization
- **Custom dashboard** showing pipeline health
- Real-time trace viewer for debugging

---

## 7. OBSERVABILITY IMPLEMENTATION PLAN

### Phase 1: Foundational (Week 1-2)
```
1. Add OpenTelemetry instrumentation to FastAPI
2. Add structured logging middleware
3. Instrument pipeline.py entry point
4. Add timing to each agent stage
5. Create basic Prometheus metrics
```

### Phase 2: Agent-Level (Week 3-4)
```
1. Instrument Intent Agent LLM calls
2. Instrument Context Resolution decisions
3. Instrument Planner execution steps
4. Instrument Execution system routing
5. Add domain-specific metrics
```

### Phase 3: Deep Insights (Week 5-6)
```
1. Data transformation tracing
2. Federation confidence scoring
3. Governance rule tracking
4. Cost analytics (LLM tokens)
5. Quality metrics aggregation
```

### Phase 4: Alerting & Dashboards (Week 7-8)
```
1. Prometheus alerting rules
2. Grafana dashboards
3. Alert routing
4. SLA tracking
5. Performance profiling
```

---

## 8. CODE INSTRUMENTATION EXAMPLES

### Example 1: Middleware-Level Tracing
```python
# Add to main.py
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry import trace

FastAPIInstrumentor.instrument_app(app)
tracer = trace.get_tracer(__name__)
```

### Example 2: Agent-Level Spans
```python
# In intent_agent/agent.py
def run(self, user_query: str):
    with tracer.start_as_current_span("intent_agent.parse") as span:
        span.set_attribute("query", user_query)
        
        # LLM call span
        with tracer.start_as_current_span("intent_agent.llm_call"):
            result = self.model.invoke(...)
        
        span.set_attribute("confidence", result.confidence_score)
        return result
```

### Example 3: Custom Metrics
```python
# Add to each agent
from prometheus_client import Histogram, Counter

intent_parse_time = Histogram('intent_agent_parse_time_seconds', ...)
llm_fallback_count = Counter('llm_fallback_total', ...)
federation_success = Counter('federation_success_total', ...)
```

### Example 4: Trace Events
```python
# In execution_agent/agent.py
trace: List[Dict] = []
trace.append({
    "timestamp": datetime.utcnow(),
    "stage": "execution",
    "event": "step_executed",
    "step_id": step.id,
    "system": step.system,
    "duration_ms": duration,
    "status": "success",
    "records": result.records_count
})
```

---

## 9. KEY OBSERVABILITY INSIGHTS

### What Makes This System Unique

1. **Multi-Agent Orchestration**: Each stage has independent logic + decision quality
   - → Track confidence scores through pipeline
   - → Monitor decision consistency

2. **LLM Hybrid Architecture**: LLM + deterministic fallbacks
   - → Track LLM usage vs rule-based fallback
   - → Monitor LLM quality and cost

3. **Cross-System Federation**: Reconciling IBM + Unisys
   - → Track join key success rates
   - → Monitor amount authority violations
   - → Detect system inconsistencies

4. **Complex Data Transformations**: Intent → Context → Plan → Execution
   - → Track data shape at each stage
   - → Monitor transformation accuracy
   - → Alert on schema violations

5. **Governance & Safety**: Financial data + compliance
   - → Audit governance rule checks
   - → Monitor amount deduplication
   - → Track approval workflows

---

## 10. NEXT STEPS

### Immediate Actions
1. ✓ Understand pipeline architecture (THIS DOCUMENT)
2. → Select observability tooling (OpenTelemetry, Prometheus, Grafana)
3. → Design metric schema
4. → Implement Phase 1 instrumentation
5. → Create baseline dashboards

### Measurement Success
- Pipeline latency breakdown < 3000ms total
- LLM fallback rate < 5% of requests
- Federation confidence > 0.85 for valid queries
- Zero governance rule violations
- < 0.1% data loss in normalization

