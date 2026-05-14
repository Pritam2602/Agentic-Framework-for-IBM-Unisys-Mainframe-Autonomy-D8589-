# Observability Instrumentation Guide - Detailed Implementation

## 1. PIPELINE ARCHITECTURE WITH OBSERVABILITY POINTS

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER REQUEST ENTRY                                │
│  POST /api/pipeline/run                                                     │
│  OBSERVE: request_id, user_query, timestamp                                │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                     ┌───────▼──────┐
                     │  MIDDLEWARE  │ ← TRACE START
                     │ (Correlation)│   - Assign request_id (UUID)
                     │              │   - Emit "pipeline_started" metric
                     └───────┬──────┘
                             │
        ┌────────────────────┴────────────────────┐
        │                                         │
    ┌───▼────────────────────────────┐    ┌──────▼──────────────────────┐
    │  [1] INTENT AGENT (WHAT)       │    │ OBSERVABILITY POINTS        │
    │  ─────────────────────────     │    │ ──────────────────────      │
    │  Input: user_query             │    │ • query_received (counter)  │
    │  Output: IntentOutput          │    │ • intent_parse_time_ms      │
    │                                │    │ • entity_detected (count)   │
    │  - Parse entity               │    │ • task_identified           │
    │  - Extract filters            │    │ • llm_call_latency_ms       │
    │  - Calculate confidence (0-1) │    │ • fallback_invoked (bool)   │
    │  - Output mode selection      │    │ • intent_confidence_score   │
    │                                │    │ • filters_extracted (count) │
    │  FALLBACK: Rule-based extract │    │ • llm_tokens_used           │
    │  if LLM fails                 │    │ • intent_agent_status       │
    └───┬────────────────────────────┘    │                             │
        │                                 └─────────────────────────────┘
        │ IntentOutput
        │ {entities, task, filters, metric, aggregation, confidence}
        │
    ┌───▼────────────────────────────┐    ┌──────────────────────────────┐
    │  [2] CONTEXT RESOLUTION (WHERE)│    │ OBSERVABILITY POINTS        │
    │  ──────────────────────────────│    │ ──────────────────────      │
    │  Input: IntentOutput           │    │ • context_resolution_start  │
    │  Output: ContextOutput         │    │ • ibm_lookup_latency_ms     │
    │                                │    │ • unisys_lookup_latency_ms  │
    │  - Resolve IBM metadata        │    │ • entity_found (bool)       │
    │    (program, dataset, JCL)     │    │ • system_confidence_ibm     │
    │  - Resolve Unisys metadata     │    │ • system_confidence_unisys  │
    │    (API, fields, tool)         │    │ • programs_found (count)    │
    │  - Calculate confidence        │    │ • datasets_found (count)    │
    │                                │    │ • apis_found (count)        │
    │  FALLBACK: Use catalog         │    │ • resolution_confidence     │
    │  if LLM fails                 │    │ • context_agent_status      │
    └───┬────────────────────────────┘    │                             │
        │                                 └─────────────────────────────┘
        │ ContextOutput
        │ {ibm: {program, dataset, jcl}, unisys: {api, fields}}
        │
    ┌───▼────────────────────────────┐    ┌──────────────────────────────┐
    │  [3] PLANNER (HOW)             │    │ OBSERVABILITY POINTS        │
    │  ───────────────────────────   │    │ ──────────────────────      │
    │  Input: Intent + Context       │    │ • planner_start             │
    │  Output: ExecutionPlan (DAG)   │    │ • dag_nodes_created (count) │
    │                                │    │ • dependencies_found (count)│
    │  - Build execution DAG         │    │ • command_candidates (count)│
    │  - Classify risks (L/M/H/C)    │    │ • governance_rules_checked  │
    │  - Select commands             │    │ • llm_refinement_time_ms    │
    │  - Add safety guards           │    │ • step_types_distribution   │
    │                                │    │ • systems_targeted (IBM/Uni)│
    │  CONSTRAINT: Cannot invent     │    │ • planner_status            │
    │  commands/systems              │    │ • plan_validity (bool)      │
    └───┬────────────────────────────┘    │                             │
        │                                 └─────────────────────────────┘
        │ PlannerOutput
        │ {steps: [{id, system, action, risk, dependencies}]}
        │
    ┌───▼────────────────────────────┐    ┌──────────────────────────────┐
    │  [4] EXECUTION AGENT (RUN)     │    │ OBSERVABILITY POINTS        │
    │  ──────────────────────────────│    │ ──────────────────────      │
    │  Input: ExecutionPlan          │    │ • execution_start           │
    │  Output: ExecutionResult       │    │ • step_initiated (per step) │
    │                                │    │ • executor_routed_to:       │
    │  - Normalize plan              │    │   - job_executor            │
    │  - Route to executors:         │    │   - dataset_executor        │
    │    * JobExecutor (JCL)         │    │   - workflow_executor       │
    │    * DatasetExecutor           │    │   - mock_zos_simulator      │
    │    * WorkflowExecutor          │    │   - shopping_service        │
    │    * MockZOS                   │    │   - inventory_service       │
    │    * MockUnisys Services       │    │ • step_duration_ms          │
    │  - Collect results             │    │ • records_returned (per step│
    │  - Handle errors               │    │ • step_errors (count)       │
    │                                │    │ • execution_status          │
    │  MODE: safe_mock by default    │    │ • total_execution_time_ms   │
    │                                │    │ • error_details (type, msg) │
    └───┬────────────────────────────┘    │                             │
        │                                 └─────────────────────────────┘
        │ ExecutionResult
        │ {status, steps_executed, step_results: [{records, errors}]}
        │
    ┌───▼────────────────────────────┐    ┌──────────────────────────────┐
    │  [5] NORMALIZATION AGENT       │    │ OBSERVABILITY POINTS        │
    │  ──────────────────────────────│    │ ──────────────────────      │
    │  Input: ExecutionResult        │    │ • normalization_start       │
    │  Output: NormalizedRecords     │    │ • records_input (count)     │
    │                                │    │ • records_output (count)    │
    │  - Map fields to canonical     │    │ • records_dropped (count)   │
    │  - Validate schema             │    │ • transformation_errors     │
    │  - Enforce amount rules:       │    │ • amount_authority_check    │
    │    * IBM is TRUTH              │    │ • join_key_validation       │
    │    * Unisys is enrichment      │    │ • schema_violations (count) │
    │  - Deduplicate amounts         │    │ • governance_checks_passed  │
    │  - Generate warnings           │    │ • normalization_status      │
    │                                │    │ • normalization_duration_ms │
    │  RULE: Never add amounts       │    │ • canonical_fields_mapped   │
    │                                │    │ • warnings_generated (count)│
    └───┬────────────────────────────┘    │                             │
        │                                 └─────────────────────────────┘
        │ NormalizedRecords
        │ {entity, records: [{customerId, amount, date, ...}]}
        │
    ┌───▼────────────────────────────┐    ┌──────────────────────────────┐
    │  [6] FEDERATION INTELLIGENCE   │    │ OBSERVABILITY POINTS        │
    │  ──────────────────────────────│    │ ──────────────────────      │
    │  Input: NormalizedRecords      │    │ • federation_discovery_start│
    │  Output: FederatedView         │    │ • capabilities_discovered   │
    │                                │    │ • entity_relationships      │
    │  - Build entity graph          │    │ • join_keys_identified      │
    │  - Discover relationships      │    │ • candidate_views (count)   │
    │  - Resolve join keys           │    │ • lineage_records_created   │
    │  - Evaluate confidence         │    │ • governance_metadata       │
    │  - Recommend view              │    │ • view_recommendation_score │
    │  - Build lineage               │    │ • federation_confidence     │
    │                                │    │ • federated_entities (count)│
    │  CONSTRAINT: Respect IBM as    │    │ • relationships_validated   │
    │  financial authority           │    │ • federation_status         │
    │                                │    │ • federation_duration_ms    │
    └───┬────────────────────────────┘    │                             │
        │                                 └─────────────────────────────┘
        │ FederatedView
        │ {name, entities, relationships, lineage, confidence}
        │
        └────────────────────┬─────────────────────────────────┐
                             │                                 │
                     ┌───────▼──────────┐          ┌──────────▼──────┐
                     │  SUCCESS RESPONSE │          │ ERROR RESPONSE  │
                     │  PipelineResponse │          │ HTTP 500        │
                     │  - All stages data│          │ + error context │
                     │  - Summary        │          │ + trace ID      │
                     │  - Confidence     │          └─────────────────┘
                     │                  │
                     │ OBSERVE:          │
                     │ • pipeline_success│
                     │ • end_to_end_time │
                     │ • success_rate    │
                     │ • failed_stage    │
                     └────────────────────┘
```

---

## 2. DETAILED INSTRUMENTATION BY STAGE

### Stage 1: Intent Agent Instrumentation

```python
# File: intent_agent/agent.py

class IntentAgent:
    def run(self, user_query: str) -> IntentOutput:
        with tracer.start_as_current_span("intent_agent.run") as span:
            start_time = time.time()
            span.set_attribute("query", user_query)
            span.set_attribute("query_length", len(user_query))
            
            # Attempt LLM
            llm_success = False
            with tracer.start_as_current_span("intent_agent.llm_call"):
                try:
                    result = self._llm_parse(user_query)
                    llm_success = True
                except Exception as e:
                    logger.warning(f"LLM failed, using fallback: {e}")
                    metrics_llm_fallback.inc()
                    result = self._rule_based_fallback(user_query)
            
            span.set_attribute("llm_success", llm_success)
            span.set_attribute("entities", result.entities)
            span.set_attribute("task", result.task)
            span.set_attribute("confidence_score", result.confidence_score)
            
            # Metrics
            metrics_intent_time.observe(time.time() - start_time)
            metrics_intent_confidence.observe(result.confidence_score)
            metrics_entities_detected.inc(len(result.entities))
            
            return result

# Metrics Definition
intent_parse_time = Histogram(
    'intent_agent_parse_time_seconds',
    'Time to parse intent',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)
intent_confidence = Gauge(
    'intent_agent_confidence_score',
    'Confidence score of parsed intent'
)
llm_fallback_count = Counter(
    'llm_fallback_total',
    'Number of times LLM fallback was used',
    ['stage']
)
```

### Stage 2: Context Resolution Instrumentation

```python
# File: context_resolution_agent/agent.py

class ContextResolutionAgent:
    async def resolve_async(self, intent: Dict) -> ContextOutput:
        with tracer.start_as_current_span("context_resolution.resolve") as span:
            start_time = time.time()
            span.set_attribute("intent_entities", intent['entities'])
            
            # IBM Resolution
            with tracer.start_as_current_span("context_resolution.ibm_lookup"):
                ibm_start = time.time()
                ibm_context = await self._resolve_ibm(intent)
                span.set_attribute("ibm_program", ibm_context.program)
                span.set_attribute("ibm_dataset", ibm_context.dataset)
                metrics_ibm_lookup_time.observe(time.time() - ibm_start)
            
            # Unisys Resolution
            with tracer.start_as_current_span("context_resolution.unisys_lookup"):
                unisys_start = time.time()
                unisys_context = await self._resolve_unisys(intent)
                span.set_attribute("unisys_api", unisys_context.api)
                metrics_unisys_lookup_time.observe(time.time() - unisys_start)
            
            context = ContextOutput(ibm=ibm_context, unisys=unisys_context)
            context.resolution_confidence = self._calculate_confidence(context)
            
            span.set_attribute("resolution_confidence", context.resolution_confidence)
            metrics_context_time.observe(time.time() - start_time)
            
            return context

# Metrics
context_resolution_time = Histogram(
    'context_resolution_time_seconds',
    'Time to resolve context'
)
ibm_lookup_time = Histogram(
    'ibm_lookup_time_seconds',
    'Time to resolve IBM context'
)
unisys_lookup_time = Histogram(
    'unisys_lookup_time_seconds',
    'Time to resolve Unisys context'
)
```

### Stage 3: Planner Instrumentation

```python
# File: planner_agent/agent.py

class PlannerAgent:
    def run(self, intent: Dict, context: Dict, use_llm: bool) -> PlannerOutput:
        with tracer.start_as_current_span("planner.run") as span:
            start_time = time.time()
            
            # Build DAG
            with tracer.start_as_current_span("planner.dag_build"):
                plan = self._build_grounded_plan(intent, context)
                span.set_attribute("dag_nodes", len(plan.steps))
                span.set_attribute("dag_edges", self._count_dependencies(plan))
            
            # LLM Refinement
            if use_llm:
                with tracer.start_as_current_span("planner.llm_refinement"):
                    llm_start = time.time()
                    self._apply_llm_refinement(plan, intent, context)
                    metrics_planner_llm_time.observe(time.time() - llm_start)
            
            # Risk Assessment
            risk_distribution = self._assess_risks(plan)
            span.set_attribute("risk_critical", risk_distribution.get("CRITICAL", 0))
            span.set_attribute("risk_high", risk_distribution.get("HIGH", 0))
            
            # System Distribution
            systems_targeted = set(step.system for step in plan.steps)
            span.set_attribute("systems_targeted", list(systems_targeted))
            
            metrics_planner_time.observe(time.time() - start_time)
            metrics_dag_nodes.observe(len(plan.steps))
            
            return PlannerAgentResponse(plan=plan, status="valid")

# Metrics
planner_time = Histogram(
    'planner_time_seconds',
    'Time to generate execution plan'
)
dag_nodes = Gauge(
    'dag_nodes_count',
    'Number of nodes in execution DAG'
)
```

### Stage 4: Execution Instrumentation

```python
# File: execution_agent/agent.py

class ExecutionAgent:
    def run(self, planner_json: Dict, ...) -> ExecutionResult:
        with tracer.start_as_current_span("execution.run") as parent_span:
            start_time = time.time()
            results = []
            
            for step in planner_json['steps']:
                with tracer.start_as_current_span(
                    f"execution.step_{step['order']}"
                ) as step_span:
                    step_start = time.time()
                    step_span.set_attribute("step_id", step['step_id'])
                    step_span.set_attribute("system", step['system'])
                    step_span.set_attribute("step_type", step['step_type'])
                    
                    # Route to appropriate executor
                    try:
                        if step['system'] == 'ibm':
                            result = self._execute_ibm_step(step)
                        else:
                            result = self._execute_unisys_step(step)
                        
                        step_span.set_attribute("status", "success")
                        step_span.set_attribute("records_returned", result.records_count)
                        metrics_execution_step_time.labels(
                            system=step['system']
                        ).observe(time.time() - step_start)
                        metrics_step_success.inc()
                        
                    except Exception as e:
                        step_span.set_attribute("status", "error")
                        step_span.record_exception(e)
                        metrics_execution_errors.inc()
                        logger.error(f"Step {step['step_id']} failed: {e}")
                    
                    results.append(result)
            
            parent_span.set_attribute("steps_executed", len(results))
            metrics_execution_time.observe(time.time() - start_time)
            
            return ExecutionResult(status="completed", step_results=results)

# Metrics
execution_time = Histogram(
    'execution_time_seconds',
    'Total execution time'
)
execution_step_time = Histogram(
    'execution_step_time_seconds',
    'Per-step execution time',
    ['system']
)
execution_errors = Counter(
    'execution_errors_total',
    'Number of execution errors'
)
```

### Stage 5: Normalization Instrumentation

```python
# File: normalization_agent/agent.py

class NormalizationAgent:
    def run(self, execution_output: Dict, ...) -> NormalizationResult:
        with tracer.start_as_current_span("normalization.run") as span:
            start_time = time.time()
            
            # Track input
            input_records = len(execution_output.get('records', []))
            span.set_attribute("input_records", input_records)
            
            # Normalization process
            with tracer.start_as_current_span("normalization.field_mapping"):
                canonical_records = self._map_fields(execution_output)
            
            # Validation
            with tracer.start_as_current_span("normalization.validation"):
                validation_result = self._validate_schema(canonical_records)
                span.set_attribute("schema_violations", len(validation_result.violations))
                metrics_schema_violations.inc(len(validation_result.violations))
            
            # Amount Authority Check (CRITICAL RULE)
            with tracer.start_as_current_span("normalization.amount_authority"):
                amount_issues = self._check_amount_authority(canonical_records)
                span.set_attribute("amount_conflicts", len(amount_issues))
                if amount_issues:
                    metrics_amount_authority_violations.inc(len(amount_issues))
            
            output_records = len(canonical_records)
            dropped = input_records - output_records
            
            span.set_attribute("output_records", output_records)
            span.set_attribute("records_dropped", dropped)
            
            metrics_normalization_time.observe(time.time() - start_time)
            metrics_records_processed.observe(input_records)
            
            return NormalizationResult(canonical_records=canonical_records)

# Metrics
normalization_time = Histogram(
    'normalization_time_seconds',
    'Time to normalize records'
)
schema_violations = Counter(
    'schema_violations_total',
    'Number of schema violations'
)
amount_authority_violations = Counter(
    'amount_authority_violations_total',
    'Violations of amount authority rule'
)
```

### Stage 6: Federation Intelligence Instrumentation

```python
# File: federation_intelligence/agent.py

def run_federation_intelligence(...) -> FederationIntelligenceOutput:
    with tracer.start_as_current_span("federation_intelligence.run") as span:
        start_time = time.time()
        
        # Discovery
        with tracer.start_as_current_span("federation_intelligence.discovery"):
            capabilities = discover_capabilities(context, metadata)
            span.set_attribute("capabilities_found", len(capabilities))
        
        # Entity Graph Building
        with tracer.start_as_current_span("federation_intelligence.entity_graph"):
            entity_graph = build_entity_graph(normalized_output, capabilities)
            span.set_attribute("entities", len(entity_graph.nodes))
            span.set_attribute("relationships", len(entity_graph.edges))
            metrics_entity_relationships.observe(len(entity_graph.edges))
        
        # Join Key Resolution
        with tracer.start_as_current_span("federation_intelligence.join_key_resolution"):
            join_results = resolve_join_key(entity_graph, normalized_output)
            span.set_attribute("join_keys_found", len(join_results.valid_joins))
            span.set_attribute("join_key_mismatches", len(join_results.mismatches))
            if join_results.mismatches:
                metrics_join_key_failures.inc(len(join_results.mismatches))
        
        # View Recommendation
        with tracer.start_as_current_span("federation_intelligence.view_recommendation"):
            views = recommend_views(entity_graph, intent, normalized_output)
            best_view = max(views, key=lambda v: v.confidence)
            span.set_attribute("views_recommended", len(views))
            span.set_attribute("recommended_view", best_view.name)
            span.set_attribute("view_confidence", best_view.confidence)
            metrics_federation_confidence.observe(best_view.confidence)
        
        metrics_federation_time.observe(time.time() - start_time)
        
        return FederationIntelligenceOutput(
            top_view=best_view,
            entity_relationships=entity_graph.edges,
            overall_confidence=best_view.confidence
        )

# Metrics
federation_time = Histogram(
    'federation_time_seconds',
    'Federation intelligence analysis time'
)
entity_relationships = Gauge(
    'entity_relationships_count',
    'Number of discovered entity relationships'
)
federation_confidence = Gauge(
    'federation_confidence_score',
    'Confidence in federated view'
)
join_key_failures = Counter(
    'join_key_failures_total',
    'Join key mismatches'
)
```

---

## 3. MIDDLEWARE INSTRUMENTATION

```python
# File: app/middleware/observability.py

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
import uuid

tracer = trace.get_tracer(__name__)
metrics_meter = metrics.get_meter(__name__)

@app.middleware("http")
async def add_trace_context(request: Request, call_next):
    """Add correlation ID and trace context to all requests"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    
    with tracer.start_as_current_span("http.request") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", request.url.path)
        span.set_attribute("request_id", request_id)
        
        response = await call_next(request)
        
        span.set_attribute("http.status_code", response.status_code)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = span.get_span_context().trace_id
        
        return response

def setup_observability():
    """Initialize observability (tracing, metrics, logging)"""
    
    # Jaeger Tracing
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Prometheus Metrics
    prometheus_reader = PrometheusMetricReader()
    metrics.set_meter_provider(MeterProvider(metric_readers=[prometheus_reader]))
    
    # FastAPI Instrumentation
    FastAPIInstrumentor.instrument_app(app)
    
    logger.info("Observability initialized (Jaeger + Prometheus)")
```

---

## 4. ALERT RULES (Prometheus)

```yaml
# File: prometheus/alert_rules.yml

groups:
  - name: agentic_framework
    interval: 30s
    rules:
      - alert: PipelineLatenessHigh
        expr: pipeline_total_end_to_end_ms > 3000
        for: 5m
        annotations:
          summary: "Pipeline latency high (> 3s)"
      
      - alert: LLMFallbackRate
        expr: rate(llm_fallback_total[5m]) > 0.05
        for: 10m
        annotations:
          summary: "LLM fallback rate > 5%"
      
      - alert: FederationConfidenceLow
        expr: federation_confidence_score < 0.5
        for: 1m
        annotations:
          summary: "Federation confidence < 50%"
      
      - alert: ExecutionErrors
        expr: rate(execution_errors_total[5m]) > 0
        for: 5m
        annotations:
          summary: "Execution errors detected"
      
      - alert: AmountAuthorityViolation
        expr: increase(amount_authority_violations_total[1h]) > 0
        for: 1m
        annotations:
          summary: "CRITICAL: Amount authority rule violated"
      
      - alert: JoinKeyMismatch
        expr: increase(join_key_failures_total[1h]) > 5
        for: 5m
        annotations:
          summary: "Join key failures detected (possible data inconsistency)"
      
      - alert: SchemaViolations
        expr: schema_violations_total > 10
        for: 10m
        annotations:
          summary: "Schema violations accumulating"
```

---

## 5. GRAFANA DASHBOARD JSON

Create a dashboard with these panels:

```json
{
  "dashboard": {
    "title": "COMMUNICATOR - Pipeline Health",
    "panels": [
      {
        "title": "Pipeline End-to-End Time",
        "targets": [
          {
            "expr": "pipeline_total_end_to_end_ms"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Stage Breakdown",
        "targets": [
          {"expr": "intent_agent_parse_time_seconds"},
          {"expr": "context_resolution_time_seconds"},
          {"expr": "planner_time_seconds"},
          {"expr": "execution_time_seconds"},
          {"expr": "normalization_time_seconds"},
          {"expr": "federation_time_seconds"}
        ],
        "type": "table"
      },
      {
        "title": "Confidence Scores",
        "targets": [
          {"expr": "intent_agent_confidence_score"},
          {"expr": "context_resolution_confidence"},
          {"expr": "federation_confidence_score"}
        ],
        "type": "gauge"
      },
      {
        "title": "Error Rates",
        "targets": [
          {"expr": "rate(execution_errors_total[5m])"},
          {"expr": "rate(amount_authority_violations_total[5m])"},
          {"expr": "rate(schema_violations_total[5m])"}
        ],
        "type": "graph"
      },
      {
        "title": "LLM Usage",
        "targets": [
          {"expr": "llm_fallback_total"},
          {"expr": "llm_tokens_used_total"}
        ],
        "type": "stat"
      },
      {
        "title": "Federation Relationships",
        "targets": [
          {"expr": "entity_relationships_count"},
          {"expr": "join_key_failures_total"}
        ],
        "type": "stat"
      }
    ]
  }
}
```

---

## 6. LOGGING STRUCTURED FORMAT

```python
# File: app/logging_config.py

import json
import logging

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""
    
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "unknown"),
            "trace_id": getattr(record, "trace_id", "unknown"),
        }
        
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj)

# Usage in agents:
logger = logging.getLogger(__name__)

# Example
logger.info(
    "Intent parsed",
    extra={
        "request_id": request_id,
        "entities": intent.entities,
        "confidence": intent.confidence_score
    }
)
```

---

## 7. NEXT IMPLEMENTATION STEPS

1. **Choose Tools**: OpenTelemetry, Jaeger, Prometheus, Grafana
2. **Set up Infrastructure**: Docker Compose for observability stack
3. **Implement Middleware**: Add request/response tracing
4. **Instrument Agents**: Follow patterns above for each stage
5. **Create Dashboards**: Build Grafana dashboards
6. **Set up Alerts**: Configure Prometheus alerting
7. **Test & Monitor**: Validate observability works end-to-end

