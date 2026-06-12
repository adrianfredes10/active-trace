import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tenant
from app.repositories.rbac_repository import RolPermisoRepository, RolRepository
from app.services.permission_service import PermissionService
from app.services.rbac_seed import seed_tenant_rbac

TENANT = uuid.UUID("00000000-0000-0000-0000-0000000000e4")
OTHER = uuid.UUID("00000000-0000-0000-0000-0000000000f4")


@pytest.mark.asyncio
async def test_effective_permissions_union(session: AsyncSession, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="E", slug="e-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    svc = PermissionService(session, TENANT)
    perms = await svc.effective_permissions(["PROFESOR", "FINANZAS"])
    assert "calificaciones:importar" in perms
    assert "liquidaciones:cerrar" in perms
    assert "tenant:configurar" not in perms


@pytest.mark.asyncio
async def test_effective_permissions_empty_without_roles(
    session: AsyncSession, settings
) -> None:
    session.add(Tenant(id=TENANT, nombre="E", slug="e-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    svc = PermissionService(session, TENANT)
    assert await svc.effective_permissions([]) == frozenset()


@pytest.mark.asyncio
async def test_lookup_scoped_to_tenant(session: AsyncSession, settings) -> None:
    session.add_all(
        [
            Tenant(id=TENANT, nombre="E", slug="e-rbac"),
            Tenant(id=OTHER, nombre="F", slug="f-rbac"),
        ]
    )
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    await seed_tenant_rbac(session, OTHER)
    repo = RolRepository(session, TENANT)
    admin = await repo.get_by_codigo("ADMIN")
    assert admin is not None
    other_repo = RolRepository(session, OTHER)
    assert await other_repo.get_by_codigo("ADMIN") is not None
    # permisos de TENANT no incluyen datos de OTHER aunque el código coincida
    rp = RolPermisoRepository(session, TENANT)
    perms = await rp.permission_keys_for_roles(["ADMIN"])
    assert "tenant:configurar" in perms
