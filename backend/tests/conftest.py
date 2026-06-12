import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import Settings, get_settings
from app.core.database import Base, dispose_db, get_session_factory, init_db
from app.core.security import EncryptedString
from app.main import create_app
from app.models.base import TenantScopedMixin


class SampleEntity(Base, TenantScopedMixin):
    """Entidad de prueba tenant-scoped, con una columna cifrada.

    Existe solo para los tests de mixins, aislamiento y cifrado: no es
    parte del dominio. Se registra en `Base.metadata` y la fixture
    `db_schema` la crea/elimina por test.
    """

    __tablename__ = "sample_entities"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    secret: Mapped[str | None] = mapped_column(EncryptedString(255), nullable=True)

VALID_SECRET_KEY = "a" * 32
VALID_ENCRYPTION_KEY = "b" * 32
DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://activia:activia@localhost:5432/activia_test"
)


def _configure_test_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    database_url: str | None = None,
    secret_key: str | None = None,
    encryption_key: str | None = None,
    access_token_expire_minutes: str | None = None,
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        database_url
        or os.getenv("TEST_DATABASE_URL")
        or DEFAULT_DATABASE_URL,
    )
    monkeypatch.setenv("SECRET_KEY", secret_key or VALID_SECRET_KEY)
    monkeypatch.setenv("ENCRYPTION_KEY", encryption_key or VALID_ENCRYPTION_KEY)
    if access_token_expire_minutes is not None:
        monkeypatch.setenv(
            "ACCESS_TOKEN_EXPIRE_MINUTES",
            access_token_expire_minutes,
        )
    get_settings.cache_clear()


@pytest.fixture
def settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    _configure_test_env(monkeypatch)
    return get_settings()


@pytest_asyncio.fixture
async def db_engine(settings: Settings):
    init_db(settings.database_url)
    yield
    await dispose_db()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def db_schema(db_engine):
    """Create all tables on the test DB and drop them after the test."""
    import app.models  # noqa: F401  ensure models are registered on Base
    from app.core.database import Base, get_engine

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
                RETURNS trigger AS $$
                BEGIN
                    RAISE EXCEPTION 'audit_logs is append-only';
                END;
                $$ LANGUAGE plpgsql;
                """
            )
        )
        await conn.execute(
            text("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs")
        )
        await conn.execute(
            text(
                """
                CREATE TRIGGER audit_logs_no_update
                BEFORE UPDATE OR DELETE ON audit_logs
                FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation()
                """
            )
        )
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def session(db_schema):
    """Async session bound to a freshly created schema."""
    session_factory = get_session_factory()
    async with session_factory() as async_session:
        yield async_session


@pytest_asyncio.fixture
async def client(db_engine):
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture
async def api_client(db_schema):
    """Cliente HTTP contra un schema recién creado (engine ya inicializado)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture(autouse=True)
def _reset_login_rate_limiter():
    from app.core.rate_limit import login_rate_limiter

    login_rate_limiter.reset()
    yield
    login_rate_limiter.reset()


@pytest.fixture
def invalid_settings_factory(monkeypatch: pytest.MonkeyPatch):
    def _build(**overrides: str | None) -> Settings:
        _configure_test_env(monkeypatch, **overrides)
        return get_settings()

    return _build


@pytest.fixture
def expect_settings_validation_error():
    def _expect(build) -> None:
        get_settings.cache_clear()
        with pytest.raises(ValidationError):
            build()

    return _expect
