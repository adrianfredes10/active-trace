from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.main import create_app


@pytest.mark.asyncio
async def test_health_returns_ok_with_database_up(client):
    response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "up"


@pytest.mark.asyncio
async def test_health_reports_database_down_without_crashing(db_engine):
    async def failing_get_db() -> AsyncGenerator[AsyncSession, None]:
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(side_effect=RuntimeError("db unavailable"))
        try:
            yield session
        finally:
            await session.close()

    app = create_app()
    app.dependency_overrides[get_db] = failing_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "down"
