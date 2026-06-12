import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant, TenantEstado


@pytest.mark.asyncio
async def test_create_tenant_defaults(session: AsyncSession) -> None:
    tenant = Tenant(nombre="Instituto Demo", slug="demo")
    session.add(tenant)
    await session.flush()

    assert isinstance(tenant.id, uuid.UUID)
    assert tenant.estado is TenantEstado.ACTIVO
    assert tenant.created_at is not None
    assert tenant.deleted_at is None


@pytest.mark.asyncio
async def test_tenant_slug_is_unique(session: AsyncSession) -> None:
    session.add(Tenant(nombre="Uno", slug="dup"))
    await session.flush()
    session.add(Tenant(nombre="Dos", slug="dup"))
    with pytest.raises(IntegrityError):
        await session.flush()


def test_tenant_has_no_tenant_id_column() -> None:
    assert "tenant_id" not in Tenant.__table__.columns
