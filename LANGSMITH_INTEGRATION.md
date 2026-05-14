# LangSmith Integration

COMMUNICATOR includes optional LangSmith tracing hooks for the six-stage federation pipeline.

## Enable Tracing

Set these environment variables before starting FastAPI:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-key>
LANGSMITH_PROJECT=communicator-federation
```

If LangSmith is not configured, the application still runs normally. The tracing helpers are no-ops.

## What Is Traced

- Pipeline request ID
- User query
- Intent stage
- Context resolution stage
- Planner stage
- Execution stage
- Normalization stage
- Federation Intelligence stage
- Individual pipeline stage contexts through the observability telemetry wrapper

LLM usage is recorded when response metadata exposes token counts. Local entries are available at:

```text
/api/observability/llm-usage
```

## Local Metrics

Prometheus-compatible metrics are exposed at:

```text
/metrics
/api/observability/metrics
```

Runtime summaries are exposed at:

```text
/api/observability/summary
/api/observability/runs
/api/observability/events
/api/observability/stream
/api/observability/llm-usage
```

## Frontend

The Control Center includes an **Observability** panel showing:

- Request ID
- Total duration
- Pipeline status
- Per-stage timings
- Stage reasoning
- Amount-authority and join-key checks
