# COMMUNICATOR Observability Assets

## Prometheus

Scrape either endpoint:

```text
http://localhost:8000/metrics
http://localhost:8000/api/observability/metrics
```

Alert rules:

```text
observability/prometheus_alerts.yml
```

## Grafana

Import:

```text
observability/grafana_dashboard.json
```

The dashboard expects a Prometheus data source and these metric names:

- `communicator_pipeline_success_rate`
- `communicator_pipeline_duration_ms`
- `communicator_stage_duration_ms`
- `communicator_join_key_match_rate`
- `communicator_amount_authority_violations_total`
- `communicator_llm_tokens_total`

## OpenTelemetry / Jaeger

Set:

```env
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
```

The app instruments FastAPI and each pipeline stage. If exporters are not installed
or not reachable, the app continues with local observability.

## LangSmith

Set:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-key>
LANGSMITH_PROJECT=communicator-federation
```

Pipeline stages use optional LangSmith trace contexts. LLM token usage is also
persisted locally in SQLite.
