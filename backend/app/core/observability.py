from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider


def setup_observability(
    app: FastAPI,
    *,
    enabled: bool,
    service_name: str,
) -> None:
    if not enabled:
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)
