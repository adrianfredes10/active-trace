import pytest
from sqlalchemy import text

from app.core.database import get_session_factory
from app.core.dependencies import get_db


@pytest.mark.asyncio
async def test_database_session_executes_select_one(db_session):
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_get_db_closes_session_on_exception(db_engine, monkeypatch):
    close_events: list[str] = []
    real_factory = get_session_factory()

    class TrackingSessionMaker:
        def __call__(self):
            session = real_factory()
            original_close = session.close

            async def close_and_track():
                close_events.append("closed")
                await original_close()

            session.close = close_and_track  # type: ignore[method-assign]
            return session

    monkeypatch.setattr(
        "app.core.dependencies.get_session_factory",
        lambda: TrackingSessionMaker(),
    )

    generator = get_db()
    await generator.__anext__()

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    assert close_events == ["closed"]
