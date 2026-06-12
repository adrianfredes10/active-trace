import uuid

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.dependencies import CurrentUser
from app.core.permissions import get_effective_permissions, require_permission
from app.models import Tenant
from app.services.rbac_seed import seed_tenant_rbac

TENANT = uuid.UUID("00000000-0000-0000-0000-0000000000b4")


def _request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


@pytest.mark.asyncio
async def test_require_permission_denies_without_perm(session, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="G", slug="g-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    user = CurrentUser(id=uuid.uuid4(), tenant_id=TENANT, roles=["ALUMNO"])
    guard = require_permission("calificaciones:importar")
    perms = await get_effective_permissions(_request(), user, session)
    with pytest.raises(HTTPException) as exc:
        await guard(permissions=perms)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_permission_allows_with_perm(session, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="G", slug="g-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    user = CurrentUser(id=uuid.uuid4(), tenant_id=TENANT, roles=["ADMIN"])
    guard = require_permission("calificaciones:importar")
    perms = await get_effective_permissions(_request(), user, session)
    await guard(permissions=perms)


@pytest.mark.asyncio
async def test_permissions_cached_on_request_state(session, settings) -> None:
    session.add(Tenant(id=TENANT, nombre="G", slug="g-rbac"))
    await session.flush()
    await seed_tenant_rbac(session, TENANT)
    user = CurrentUser(id=uuid.uuid4(), tenant_id=TENANT, roles=["ADMIN"])
    req = _request()
    first = await get_effective_permissions(req, user, session)
    second = await get_effective_permissions(req, user, session)
    assert first is second
