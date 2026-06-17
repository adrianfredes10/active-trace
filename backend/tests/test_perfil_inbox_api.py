"""Tests API perfil propio e inbox interno — C-20."""

import uuid

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

TENANT_A = uuid.UUID("00000000-0000-0000-0000-000000000c20")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-00000000c20b")
SLUG_A = "c20-a"
SLUG_B = "c20-b"
EMAIL_PROF = "prof@c20.example.com"
EMAIL_COORD = "coord@c20.example.com"
EMAIL_OTHER = "other@c20.example.com"
EMAIL_B = "user@tenantb.example.com"
PW = "S3cret!pass"
CUIL_ORIGINAL = "20123456789"


async def _seed_tenant(
    tenant_id: uuid.UUID,
    slug: str,
    users: list[tuple[str, str]],
) -> dict[str, Usuario]:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=tenant_id, nombre=slug, slug=slug))
        await session.flush()
        await seed_tenant_rbac(session, tenant_id)
        out: dict[str, Usuario] = {}
        for email, role in users:
            u = await UsuarioRepository(session, tenant_id).add(
                Usuario(
                    email=email,
                    email_hash=email_blind_index(email),
                    password_hash=hash_password(PW),
                    nombre="Nombre",
                    apellidos="Apellido",
                    cuil=CUIL_ORIGINAL,
                    dni="12345678",
                    banco="Banco Test",
                    regional="Regional Sur",
                )
            )
            rol = await RolRepository(session, tenant_id).get_by_codigo(role)
            assert rol is not None
            await UsuarioRolRepository(session, tenant_id).assign_role(u.id, rol.id)
            out[email] = u
        await session.commit()
        return out


async def _headers(api_client, slug: str, email: str) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": slug, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_get_perfil_incluye_cuil_solo_lectura(api_client) -> None:
    await _seed_tenant(
        TENANT_A,
        SLUG_A,
        [(EMAIL_PROF, "PROFESOR"), (EMAIL_COORD, "COORDINADOR")],
    )
    headers = await _headers(api_client, SLUG_A, EMAIL_PROF)
    resp = await api_client.get("/api/perfil", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["cuil"] == CUIL_ORIGINAL
    assert body["nombre"] == "Nombre"
    assert body["regional"] == "Regional Sur"


@pytest.mark.asyncio
async def test_patch_perfil_actualiza_campos_editables(api_client) -> None:
    await _seed_tenant(
        TENANT_A,
        SLUG_A,
        [(EMAIL_PROF, "PROFESOR"), (EMAIL_COORD, "COORDINADOR")],
    )
    headers = await _headers(api_client, SLUG_A, EMAIL_PROF)
    resp = await api_client.patch(
        "/api/perfil",
        headers=headers,
        json={
            "nombre": "Juan",
            "apellidos": "Pérez",
            "banco": "Nuevo Banco",
            "regional": "Córdoba",
            "dni": "99887766",
            "cbu": "1234567890123456789012",
            "alias_cbu": "mi.alias",
            "facturador": True,
            "legajo_profesional": "MP-1234",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["nombre"] == "Juan"
    assert body["apellidos"] == "Pérez"
    assert body["banco"] == "Nuevo Banco"
    assert body["regional"] == "Córdoba"
    assert body["dni"] == "99887766"
    assert body["cbu"] == "1234567890123456789012"
    assert body["alias_cbu"] == "mi.alias"
    assert body["facturador"] is True
    assert body["legajo_profesional"] == "MP-1234"
    assert body["cuil"] == CUIL_ORIGINAL


@pytest.mark.asyncio
async def test_patch_perfil_rechaza_cuil_en_body(api_client) -> None:
    await _seed_tenant(TENANT_A, SLUG_A, [(EMAIL_PROF, "PROFESOR")])
    headers = await _headers(api_client, SLUG_A, EMAIL_PROF)
    resp = await api_client.patch(
        "/api/perfil",
        headers=headers,
        json={"nombre": "X", "cuil": "20999999999"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_inbox_crear_hilo_leer_y_responder(api_client) -> None:
    users = await _seed_tenant(
        TENANT_A,
        SLUG_A,
        [(EMAIL_PROF, "PROFESOR"), (EMAIL_COORD, "COORDINADOR")],
    )
    headers_coord = await _headers(api_client, SLUG_A, EMAIL_COORD)
    headers_prof = await _headers(api_client, SLUG_A, EMAIL_PROF)

    resp = await api_client.post(
        "/api/inbox/mensajes",
        headers=headers_coord,
        json={
            "destinatario_id": str(users[EMAIL_PROF].id),
            "asunto": "Coordinación semanal",
            "cuerpo": "Revisá el padrón por favor.",
        },
    )
    assert resp.status_code == 201
    hilo_id = resp.json()["hilo_id"]

    resp = await api_client.get("/api/inbox/hilos", headers=headers_prof)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["asunto"] == "Coordinación semanal"

    resp = await api_client.get(f"/api/inbox/hilos/{hilo_id}", headers=headers_prof)
    assert resp.status_code == 200
    mensajes = resp.json()["mensajes"]
    assert len(mensajes) == 1
    assert mensajes[0]["cuerpo"] == "Revisá el padrón por favor."

    resp = await api_client.post(
        f"/api/inbox/hilos/{hilo_id}/responder",
        headers=headers_prof,
        json={"cuerpo": "Listo, lo reviso hoy."},
    )
    assert resp.status_code == 201

    resp = await api_client.get(f"/api/inbox/hilos/{hilo_id}", headers=headers_coord)
    assert resp.status_code == 200
    assert len(resp.json()["mensajes"]) == 2
    assert resp.json()["mensajes"][1]["cuerpo"] == "Listo, lo reviso hoy."


@pytest.mark.asyncio
async def test_inbox_aislamiento_usuario_y_tenant(api_client) -> None:
    users_a = await _seed_tenant(
        TENANT_A,
        SLUG_A,
        [
            (EMAIL_PROF, "PROFESOR"),
            (EMAIL_COORD, "COORDINADOR"),
            (EMAIL_OTHER, "PROFESOR"),
        ],
    )
    await _seed_tenant(TENANT_B, SLUG_B, [(EMAIL_B, "PROFESOR")])

    headers_coord = await _headers(api_client, SLUG_A, EMAIL_COORD)
    resp = await api_client.post(
        "/api/inbox/mensajes",
        headers=headers_coord,
        json={
            "destinatario_id": str(users_a[EMAIL_PROF].id),
            "asunto": "Privado",
            "cuerpo": "Solo para prof.",
        },
    )
    hilo_id = resp.json()["hilo_id"]

    headers_other = await _headers(api_client, SLUG_A, EMAIL_OTHER)
    resp = await api_client.get(f"/api/inbox/hilos/{hilo_id}", headers=headers_other)
    assert resp.status_code == 404

    headers_b = await _headers(api_client, SLUG_B, EMAIL_B)
    resp = await api_client.get(f"/api/inbox/hilos/{hilo_id}", headers=headers_b)
    assert resp.status_code == 404
