from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.observability import setup_observability
from app.main import create_app


@pytest.mark.asyncio
async def test_app_starts_with_otel_enabled_without_exporter(db_engine, monkeypatch):
    monkeypatch.setenv("OTEL_ENABLED", "true")
    get_settings.cache_clear()

    app = create_app()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200


def test_setup_observability_disabled_is_noop(monkeypatch):
    instrument_mock = MagicMock()
    monkeypatch.setattr(
        "app.core.observability.FastAPIInstrumentor.instrument_app",
        instrument_mock,
    )

    app = FastAPI()
    setup_observability(app, enabled=False, service_name="activia-trace-test")

    instrument_mock.assert_not_called()


def test_setup_observability_enables_fastapi_instrumentation(monkeypatch):
    instrument_mock = MagicMock()
    monkeypatch.setattr(
        "app.core.observability.FastAPIInstrumentor.instrument_app",
        instrument_mock,
    )
    set_provider_mock = MagicMock()
    monkeypatch.setattr(
        "app.core.observability.trace.set_tracer_provider",
        set_provider_mock,
    )

    app = FastAPI()
    setup_observability(app, enabled=True, service_name="activia-trace-test")

    set_provider_mock.assert_called_once()
    instrument_mock.assert_called_once_with(app)
