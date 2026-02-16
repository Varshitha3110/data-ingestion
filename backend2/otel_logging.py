import logging
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter



def setup(service_name: str):
    # ---------- Resource ----------
    resource = Resource.create({
        "service.name": service_name
    })

    # ---------- Tracing ----------
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint="http://otel-collector:4318/v1/traces"
            )
        )
    )

    # ---------- Logging (trace context injection only) ----------
    LoggingInstrumentor().instrument(set_logging_format=True)

    # ---------- Python logging config ----------
    logging.basicConfig(
        level=logging.INFO,           # INFO for prod, DEBUG for troubleshooting
        force=True,                   # 🔑 prevents duplicate handlers
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "[service=%(name)s] "
            "[trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] "
            "[%(filename)s:%(lineno)d] "
            "%(message)s"
        ),
    )

    # Optional: reduce noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
