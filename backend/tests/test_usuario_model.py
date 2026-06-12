import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario

TENANT_A = uuid.UUID("00000000-0000-0000-0000-0000000000a3")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-0000000000b3")


async def _seed_tenants(session: AsyncSession) -> None:
    session.add_all(
        [
            Tenant(id=TENANT_A, nombre="A", slug="a"),
            Tenant(id=TENANT_B, nombre="B", slug="b"),
        ]
    )
    await session.flush()


def _usuario(tenant_id: uuid.UUID, email: str) -> Usuario:
    return Usuario(
        tenant_id=tenant_id,
        email=email,
        email_hash=email_blind_index(email),
        password_hash=hash_password("pw"),
    )


@pytest.mark.asyncio
async def test_email_unique_per_tenant(session: AsyncSession, settings) -> None:
    await _seed_tenants(session)
    session.add(_usuario(TENANT_A, "alumno@activia.test"))
    await session.flush()
    session.add(_usuario(TENANT_A, "alumno@activia.test"))
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_same_email_different_tenant_is_allowed(
    session: AsyncSession, settings
) -> None:
    await _seed_tenants(session)
    session.add(_usuario(TENANT_A, "alumno@activia.test"))
    session.add(_usuario(TENANT_B, "alumno@activia.test"))
    await session.flush()  # no debe fallar


@pytest.mark.asyncio
async def test_repr_does_not_leak_email(session: AsyncSession, settings) -> None:
    user = _usuario(TENANT_A, "alumno@activia.test")
    assert "alumno@activia.test" not in repr(user)
