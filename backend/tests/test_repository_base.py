import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant
from app.repositories.base import BaseRepository
from tests.conftest import SampleEntity

TENANT_A = uuid.UUID("00000000-0000-0000-0000-0000000000a1")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-0000000000b2")


async def _seed_tenants(session: AsyncSession) -> None:
    session.add_all(
        [
            Tenant(id=TENANT_A, nombre="A", slug="a"),
            Tenant(id=TENANT_B, nombre="B", slug="b"),
        ]
    )
    await session.flush()


def _repo(session: AsyncSession, tenant_id: uuid.UUID) -> BaseRepository[SampleEntity]:
    return BaseRepository(session, tenant_id, model=SampleEntity)


@pytest.mark.asyncio
async def test_requires_model() -> None:
    with pytest.raises(ValueError):
        BaseRepository(session=None, tenant_id=TENANT_A)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_isolated_by_tenant(session: AsyncSession) -> None:
    await _seed_tenants(session)
    entity = await _repo(session, TENANT_A).add(SampleEntity(name="secreto-A"))
    await session.flush()

    assert await _repo(session, TENANT_A).get(entity.id) is not None
    assert await _repo(session, TENANT_B).get(entity.id) is None


@pytest.mark.asyncio
async def test_list_scoped_by_tenant(session: AsyncSession) -> None:
    await _seed_tenants(session)
    await _repo(session, TENANT_A).add(SampleEntity(name="a1"))
    await _repo(session, TENANT_A).add(SampleEntity(name="a2"))
    await _repo(session, TENANT_B).add(SampleEntity(name="b1"))
    await session.flush()

    rows_a = await _repo(session, TENANT_A).list()
    assert {r.name for r in rows_a} == {"a1", "a2"}


@pytest.mark.asyncio
async def test_add_forces_context_tenant(session: AsyncSession) -> None:
    await _seed_tenants(session)
    # entidad entra con tenant_id ajeno; el repo debe sobreescribirlo
    entity = SampleEntity(tenant_id=TENANT_B, name="x")
    await _repo(session, TENANT_A).add(entity)
    await session.flush()

    assert entity.tenant_id == TENANT_A
    assert await _repo(session, TENANT_B).get(entity.id) is None


@pytest.mark.asyncio
async def test_soft_delete_excluded_by_default_and_recoverable(
    session: AsyncSession,
) -> None:
    await _seed_tenants(session)
    repo = _repo(session, TENANT_A)
    entity = await repo.add(SampleEntity(name="borrame"))
    await session.flush()

    await repo.soft_delete(entity)

    assert entity.deleted_at is not None
    assert await repo.get(entity.id) is None
    assert await repo.list() == []
    # la fila sigue existiendo físicamente, recuperable por el escape hatch
    recovered = await repo.get_including_deleted(entity.id)
    assert recovered is not None and recovered.id == entity.id


@pytest.mark.asyncio
async def test_encrypted_column_persists_ciphertext(session: AsyncSession) -> None:
    await _seed_tenants(session)
    repo = _repo(session, TENANT_A)
    dni = "20-12345678-9"
    entity = await repo.add(SampleEntity(name="alumno", secret=dni))
    await session.commit()
    entity_id = entity.id

    # lectura cruda (text() no aplica el TypeDecorator): debe ser ciphertext
    raw = await session.execute(
        text("SELECT secret FROM sample_entities WHERE id = :id"),
        {"id": entity_id},
    )
    stored = raw.scalar_one()
    assert stored != dni
    assert dni not in stored

    # lectura por ORM: descifrado transparente
    session.expire(entity)
    reloaded = await repo.get(entity_id)
    assert reloaded is not None and reloaded.secret == dni
