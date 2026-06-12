import uuid

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.audit_service import AuditContext, AuditService
from app.services.rbac_seed import seed_tenant_rbac
from app.core.audit_actions import AuditAction

pytestmark = pytest.mark.asyncio

SLUG = "audit-list"
TENANT = uuid.UUID("00000000-0000-0000-0000-000000000701")
EMAIL = "coord@audit.test"
PW = "S3cret!pass"


async def _seed() -> None:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT, nombre="AuditList", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT)
        user = await UsuarioRepository(session, TENANT).add(
            Usuario(
                email=EMAIL,
                email_hash=email_blind_index(EMAIL),
                password_hash=hash_password(PW),
            )
        )
        rol = await RolRepository(session, TENANT).get_by_codigo("COORDINADOR")
        assert rol is not None
        await UsuarioRolRepository(session, TENANT).assign_role(user.id, rol.id)
        ctx = AuditContext(actor_id=user.id, tenant_id=TENANT)
        await AuditService(session, TENANT).record(
            ctx, accion=AuditAction.CALIFICACIONES_IMPORTAR, filas_afectadas=3
        )
        await session.commit()


@pytest.mark.asyncio
async def test_list_audit_requires_auth(api_client) -> None:
    await _seed()
    assert (await api_client.get("/api/audit")).status_code == 401


@pytest.mark.asyncio
async def test_list_audit_with_permission(api_client) -> None:
    await _seed()
    login = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": EMAIL, "password": PW},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = await api_client.get("/api/audit", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["accion"] == "CALIFICACIONES_IMPORTAR"
    assert resp.json()["items"][0]["filas_afectadas"] == 3


@pytest.mark.asyncio
async def test_list_audit_denied_without_permission(api_client) -> None:
    await _seed()
    factory = get_session_factory()
    async with factory() as session:
        alumno = await UsuarioRepository(session, TENANT).add(
            Usuario(
                email="alumno@audit.test",
                email_hash=email_blind_index("alumno@audit.test"),
                password_hash=hash_password(PW),
            )
        )
        rol = await RolRepository(session, TENANT).get_by_codigo("ALUMNO")
        assert rol is not None
        await UsuarioRolRepository(session, TENANT).assign_role(alumno.id, rol.id)
        await session.commit()
    login = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": "alumno@audit.test", "password": PW},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await api_client.get("/api/audit", headers=headers)).status_code == 403
