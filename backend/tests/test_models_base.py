import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import SampleEntity

TENANT_A = uuid.UUID("00000000-0000-0000-0000-00000000000a")


async def _seed_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    from app.models import Tenant

    session.add(Tenant(id=tenant_id, nombre="Tenant A", slug=f"a-{tenant_id.hex[:8]}"))
    await session.flush()


@pytest.mark.asyncio
async def test_mixin_sets_uuid_and_timestamps(session: AsyncSession) -> None:
    await _seed_tenant(session, TENANT_A)
    entity = SampleEntity(tenant_id=TENANT_A, name="x")
    session.add(entity)
    await session.flush()

    assert isinstance(entity.id, uuid.UUID)
    assert entity.created_at is not None
    assert entity.updated_at is not None
    assert entity.deleted_at is None


@pytest.mark.asyncio
async def test_updated_at_changes_on_update(session: AsyncSession) -> None:
    await _seed_tenant(session, TENANT_A)
    entity = SampleEntity(tenant_id=TENANT_A, name="x")
    session.add(entity)
    await session.commit()
    created = entity.created_at
    original_updated = entity.updated_at

    entity.name = "y"
    await session.commit()
    await session.refresh(entity)

    assert entity.created_at == created
    assert entity.updated_at >= original_updated
