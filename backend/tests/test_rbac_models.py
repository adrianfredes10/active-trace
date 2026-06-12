import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permiso, Rol, RolPermiso, Tenant, UsuarioRol

TENANT_A = uuid.UUID("00000000-0000-0000-0000-0000000000a4")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-0000000000b4")


async def _seed_tenants(session: AsyncSession) -> None:
    session.add_all(
        [
            Tenant(id=TENANT_A, nombre="A", slug="a-rbac"),
            Tenant(id=TENANT_B, nombre="B", slug="b-rbac"),
        ]
    )
    await session.flush()


@pytest.mark.asyncio
async def test_rol_unique_per_tenant(session: AsyncSession, settings) -> None:
    await _seed_tenants(session)
    session.add(Rol(tenant_id=TENANT_A, codigo="ADMIN", nombre="Admin"))
    await session.flush()
    session.add(Rol(tenant_id=TENANT_A, codigo="ADMIN", nombre="Dup"))
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_same_rol_codigo_different_tenant(session: AsyncSession, settings) -> None:
    await _seed_tenants(session)
    session.add(Rol(tenant_id=TENANT_A, codigo="ADMIN", nombre="Admin A"))
    session.add(Rol(tenant_id=TENANT_B, codigo="ADMIN", nombre="Admin B"))
    await session.flush()


@pytest.mark.asyncio
async def test_permiso_unique_modulo_accion(session: AsyncSession, settings) -> None:
    await _seed_tenants(session)
    session.add(Permiso(tenant_id=TENANT_A, modulo="avisos", accion="confirmar"))
    await session.flush()
    session.add(Permiso(tenant_id=TENANT_A, modulo="avisos", accion="confirmar"))
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_rol_permiso_unique_pair(session: AsyncSession, settings) -> None:
    await _seed_tenants(session)
    rol = Rol(tenant_id=TENANT_A, codigo="ADMIN", nombre="Admin")
    perm = Permiso(tenant_id=TENANT_A, modulo="avisos", accion="confirmar")
    session.add_all([rol, perm])
    await session.flush()
    session.add(
        RolPermiso(tenant_id=TENANT_A, rol_id=rol.id, permiso_id=perm.id)
    )
    await session.flush()
    session.add(
        RolPermiso(tenant_id=TENANT_A, rol_id=rol.id, permiso_id=perm.id)
    )
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_usuario_rol_unique_pair(session: AsyncSession, settings) -> None:
    await _seed_tenants(session)
    from app.core.security import email_blind_index, hash_password
    from app.models import Usuario

    rol = Rol(tenant_id=TENANT_A, codigo="ADMIN", nombre="Admin")
    user = Usuario(
        tenant_id=TENANT_A,
        email="u@a.test",
        email_hash=email_blind_index("u@a.test"),
        password_hash=hash_password("pw"),
    )
    session.add_all([rol, user])
    await session.flush()
    session.add(UsuarioRol(tenant_id=TENANT_A, usuario_id=user.id, rol_id=rol.id))
    await session.flush()
    session.add(UsuarioRol(tenant_id=TENANT_A, usuario_id=user.id, rol_id=rol.id))
    with pytest.raises(IntegrityError):
        await session.flush()
