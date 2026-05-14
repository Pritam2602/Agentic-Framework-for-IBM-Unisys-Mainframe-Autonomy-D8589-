"""Optional OpenTelemetry and Jaeger/OTLP setup."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator


OTEL_ENABLED = False


def setup_opentelemetry(app: Any = None) -> None:
    """Configure tracing if OpenTelemetry dependencies are installed.

    Supported env vars:
    - OTEL_ENABLED=true
    - OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
    - JAEGER_AGENT_HOST=localhost
    - JAEGER_AGENT_PORT=6831
    """
    global OTEL_ENABLED
    if os.getenv("OTEL_ENABLED", "").lower() not in {"1", "true", "yes"}:
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception:
        return

    resource = Resource.create({"service.name": "communicator-federation"})
    provider = TracerProvider(resource=resource)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))

    try:
        # Optional legacy Jaeger exporter support if installed.
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter

        jaeger_host = os.getenv("JAEGER_AGENT_HOST")
        if jaeger_host:
            provider.add_span_processor(
                BatchSpanProcessor(
                    JaegerExporter(
                        agent_host_name=jaeger_host,
                        agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
                    )
                )
            )
    except Exception:
        pass

    trace.set_tracer_provider(provider)
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass
    OTEL_ENABLED = True


def get_tracer():
    try:
        from opentelemetry import trace

        return trace.get_tracer("communicator.observability")
    except Exception:
        return None


@contextmanager
def trace_span(name: str, **attributes: Any) -> Iterator[Any]:
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            if value is not None:
                try:
                    span.set_attribute(key, value)
                except Exception:
                    pass
        yield span
