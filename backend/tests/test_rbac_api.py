import uuid

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

pytestmark = pytest.mark.asyncio

SLUG = "rbac-api"
TENANT = uuid.UUID("00000000-0000-0000-0000-0000000000c4")
EMAIL = "rbac@activia.test"
PW = "S3cret!pass"


async def _seed_user(*, role: str | None = "ADMIN") -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT, nombre="I", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT)
        user = await UsuarioRepository(session, TENANT).add(
            Usuario(
                email=EMAIL,
                email_hash=email_blind_index(EMAIL),
                password_hash=hash_password(PW),
            )
        )
        if role:
            rol = await RolRepository(session, TENANT).get_by_codigo(role)
            assert rol is not None
            await UsuarioRolRepository(session, TENANT).assign_role(user.id, rol.id)
        await session.commit()
    return {"tenant_slug": SLUG, "email": EMAIL, "password": PW}


async def _login(api_client, payload: dict) -> dict:
    resp = await api_client.post("/api/auth/login", json=payload)
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
async def test_permisos_efectivos(api_client) -> None:
    payload = await _seed_user(role="PROFESOR")
    tokens = await _login(api_client, payload)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await api_client.get("/api/rbac/permisos-efectivos", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    perms = body["permisos"]
    assert "calificaciones:importar" in perms
    assert "tenant:configurar" not in perms
    assert body["roles"] == ["PROFESOR"]


@pytest.mark.asyncio
async def test_catalogo_lists_roles(api_client) -> None:
    payload = await _seed_user()
    tokens = await _login(api_client, payload)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await api_client.get("/api/rbac/catalogo", headers=headers)
    assert resp.status_code == 200
    codigos = {r["codigo"] for r in resp.json()["roles"]}
    assert "ADMIN" in codigos
    assert "NEXO" in codigos


@pytest.mark.asyncio
async def test_demo_protegido_403_without_permission(api_client) -> None:
    payload = await _seed_user(role="ALUMNO")
    tokens = await _login(api_client, payload)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await api_client.get("/api/rbac/demo-protegido", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_demo_protegido_200_with_permission(api_client) -> None:
    payload = await _seed_user(role="ADMIN")
    tokens = await _login(api_client, payload)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = await api_client.get("/api/rbac/demo-protegido", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["detail"] == "ok"


@pytest.mark.asyncio
async def test_rbac_endpoints_require_auth(api_client) -> None:
    await _seed_user()
    assert (await api_client.get("/api/rbac/catalogo")).status_code == 401
