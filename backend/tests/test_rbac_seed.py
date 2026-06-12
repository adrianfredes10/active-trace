import uuid

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permiso, Rol, RolPermiso, Tenant
from app.services.rbac_seed import DOMAIN_ROLES, ROLE_PERMISSION_KEYS, seed_tenant_rbac

TENANT = uuid.UUID("00000000-0000-0000-0000-0000000000c4")


@pytest.mark.asyncio
async def test_seed_creates_seven_roles(session: AsyncSession, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="C", slug="c-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    count = await session.scalar(
        select(func.count()).select_from(Rol).where(Rol.tenant_id == TENANT)
    )
    assert count == len(DOMAIN_ROLES)


@pytest.mark.asyncio
async def test_seed_idempotent(session: AsyncSession, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="C", slug="c-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    await seed_tenant_rbac(session, TENANT)
    roles = await session.scalar(
        select(func.count()).select_from(Rol).where(Rol.tenant_id == TENANT)
    )
    perms = await session.scalar(
        select(func.count()).select_from(Permiso).where(Permiso.tenant_id == TENANT)
    )
    links = await session.scalar(
        select(func.count()).select_from(RolPermiso).where(RolPermiso.tenant_id == TENANT)
    )
    assert roles == len(DOMAIN_ROLES)
    assert perms > 0
    assert links > 0


@pytest.mark.asyncio
async def test_nexo_has_no_permissions(session: AsyncSession, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="C", slug="c-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    nexo = await session.scalar(
        select(Rol.id).where(Rol.tenant_id == TENANT, Rol.codigo == "NEXO")
    )
    assert nexo is not None
    link_count = await session.scalar(
        select(func.count())
        .select_from(RolPermiso)
        .where(RolPermiso.tenant_id == TENANT, RolPermiso.rol_id == nexo)
    )
    assert link_count == 0


@pytest.mark.asyncio
async def test_admin_has_import_permission(session: AsyncSession, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="C", slug="c-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    admin_perms = set(ROLE_PERMISSION_KEYS["ADMIN"])
    assert "calificaciones:importar" in admin_perms
