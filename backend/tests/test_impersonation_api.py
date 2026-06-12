import uuid

import pytest

from app.core.database import get_session_factory
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    decode_token,
    email_blind_index,
    hash_password,
)
from app.models import Tenant, Usuario
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

pytestmark = pytest.mark.asyncio

SLUG = "impersonate-api"
TENANT = uuid.UUID("00000000-0000-0000-0000-000000000601")
ADMIN_EMAIL = "admin@imp.test"
TARGET_EMAIL = "target@imp.test"
PW = "S3cret!pass"


async def _seed_users() -> tuple[str, str]:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT, nombre="Imp", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT)
        admin = await UsuarioRepository(session, TENANT).add(
            Usuario(
                email=ADMIN_EMAIL,
                email_hash=email_blind_index(ADMIN_EMAIL),
                password_hash=hash_password(PW),
            )
        )
        target = await UsuarioRepository(session, TENANT).add(
            Usuario(
                email=TARGET_EMAIL,
                email_hash=email_blind_index(TARGET_EMAIL),
                password_hash=hash_password(PW),
            )
        )
        admin_rol = await RolRepository(session, TENANT).get_by_codigo("ADMIN")
        assert admin_rol is not None
        await UsuarioRolRepository(session, TENANT).assign_role(admin.id, admin_rol.id)
        await session.commit()
        return str(admin.id), str(target.id)


async def _login(api_client, email: str) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return resp.json()


@pytest.mark.asyncio
async def test_impersonate_start_stop_flow(api_client) -> None:
    admin_id, target_id = await _seed_users()
    tokens = await _login(api_client, ADMIN_EMAIL)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    start = await api_client.post(
        "/api/auth/impersonate/start",
        json={"target_user_id": target_id},
        headers=headers,
    )
    assert start.status_code == 200
    imp_token = start.json()["access_token"]
    claims = decode_token(imp_token, expected_type=TOKEN_TYPE_ACCESS)
    assert claims["sub"] == admin_id
    assert claims["impersonated_sub"] == target_id
    imp_headers = {"Authorization": f"Bearer {imp_token}"}
    stop = await api_client.post("/api/auth/impersonate/stop", headers=imp_headers)
    assert stop.status_code == 200
    clean = decode_token(stop.json()["access_token"], expected_type=TOKEN_TYPE_ACCESS)
    assert "impersonated_sub" not in clean


@pytest.mark.asyncio
async def test_impersonate_requires_permission(api_client) -> None:
    _, target_id = await _seed_users()
    target_tokens = await _login(api_client, TARGET_EMAIL)
    headers = {"Authorization": f"Bearer {target_tokens['access_token']}"}
    resp = await api_client.post(
        "/api/auth/impersonate/start",
        json={"target_user_id": target_id},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_impersonation_creates_audit_entries(api_client) -> None:
    _, target_id = await _seed_users()
    tokens = await _login(api_client, ADMIN_EMAIL)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    start = await api_client.post(
        "/api/auth/impersonate/start",
        json={"target_user_id": target_id},
        headers=headers,
    )
    imp_headers = {"Authorization": f"Bearer {start.json()['access_token']}"}
    await api_client.post("/api/auth/impersonate/stop", headers=imp_headers)
    audit = await api_client.get("/api/audit", headers=headers)
    assert audit.status_code == 200
    acciones = [i["accion"] for i in audit.json()["items"]]
    assert "IMPERSONACION_INICIAR" in acciones
    assert "IMPERSONACION_FINALIZAR" in acciones
