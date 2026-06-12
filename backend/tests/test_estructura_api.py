"""Tests API estructura académica (C-06)."""

import uuid
from datetime import date

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.estructura import EntidadEstado
from app.repositories.estructura_repository import CarreraRepository
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

pytestmark = pytest.mark.asyncio

TENANT_A = uuid.UUID("00000000-0000-0000-0000-0000000000e6")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-0000000000e7")
SLUG_A = "estructura-a"
SLUG_B = "estructura-b"
EMAIL_ADMIN = "admin@estructura.test"
EMAIL_PROF = "prof@estructura.test"
PW = "S3cret!pass"


async def _seed_tenant(
    *,
    tenant_id: uuid.UUID,
    slug: str,
    email: str,
    role: str,
) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=tenant_id, nombre=f"T {slug}", slug=slug))
        await session.flush()
        await seed_tenant_rbac(session, tenant_id)
        user = await UsuarioRepository(session, tenant_id).add(
            Usuario(
                email=email,
                email_hash=email_blind_index(email),
                password_hash=hash_password(PW),
            )
        )
        rol = await RolRepository(session, tenant_id).get_by_codigo(role)
        assert rol is not None
        await UsuarioRolRepository(session, tenant_id).assign_role(user.id, rol.id)
        await session.commit()
    return {"tenant_slug": slug, "email": email, "password": PW}


async def _login(api_client, payload: dict) -> str:
    resp = await api_client.post("/api/auth/login", json=payload)
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _auth_headers(api_client, *, role: str = "ADMIN") -> dict:
    payload = await _seed_tenant(
        tenant_id=TENANT_A,
        slug=SLUG_A,
        email=EMAIL_ADMIN if role == "ADMIN" else EMAIL_PROF,
        role=role,
    )
    token = await _login(api_client, payload)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_carrera_crud(api_client) -> None:
    headers = await _auth_headers(api_client)
    create = await api_client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Tecnicatura"},
        headers=headers,
    )
    assert create.status_code == 201
    carrera_id = create.json()["id"]

    listed = await api_client.get("/api/admin/carreras", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    updated = await api_client.patch(
        f"/api/admin/carreras/{carrera_id}",
        json={"nombre": "Tecnicatura Actualizada"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["nombre"] == "Tecnicatura Actualizada"

    deleted = await api_client.delete(
        f"/api/admin/carreras/{carrera_id}",
        headers=headers,
    )
    assert deleted.status_code == 204

    listed_after = await api_client.get("/api/admin/carreras", headers=headers)
    assert listed_after.json()["items"] == []


@pytest.mark.asyncio
async def test_carrera_codigo_duplicado_409(api_client) -> None:
    headers = await _auth_headers(api_client)
    first = await api_client.post(
        "/api/admin/carreras",
        json={"codigo": "DUP", "nombre": "Uno"},
        headers=headers,
    )
    assert first.status_code == 201
    second = await api_client.post(
        "/api/admin/carreras",
        json={"codigo": "DUP", "nombre": "Dos"},
        headers=headers,
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_cohorte_requiere_carrera_activa(api_client) -> None:
    headers = await _auth_headers(api_client)
    carrera = await api_client.post(
        "/api/admin/carreras",
        json={
            "codigo": "INACT",
            "nombre": "Inactiva",
            "estado": EntidadEstado.INACTIVA.value,
        },
        headers=headers,
    )
    assert carrera.status_code == 201
    carrera_id = carrera.json()["id"]

    rejected = await api_client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "AGO-2025",
            "anio": 2025,
            "vig_desde": "2025-08-01",
        },
        headers=headers,
    )
    assert rejected.status_code == 422


@pytest.mark.asyncio
async def test_cohorte_crud_y_unicidad(api_client) -> None:
    headers = await _auth_headers(api_client)
    carrera = await api_client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Tecnicatura"},
        headers=headers,
    )
    carrera_id = carrera.json()["id"]

    create = await api_client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "AGO-2025",
            "anio": 2025,
            "vig_desde": "2025-08-01",
        },
        headers=headers,
    )
    assert create.status_code == 201

    dup = await api_client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "AGO-2025",
            "anio": 2026,
            "vig_desde": "2026-08-01",
        },
        headers=headers,
    )
    assert dup.status_code == 409


@pytest.mark.asyncio
async def test_materia_crud(api_client) -> None:
    headers = await _auth_headers(api_client)
    create = await api_client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Programación I"},
        headers=headers,
    )
    assert create.status_code == 201
    materia_id = create.json()["id"]

    listed = await api_client.get("/api/admin/materias", headers=headers)
    assert len(listed.json()["items"]) == 1

    await api_client.delete(f"/api/admin/materias/{materia_id}", headers=headers)


@pytest.mark.asyncio
async def test_estructura_403_sin_permiso(api_client) -> None:
    headers = await _auth_headers(api_client, role="PROFESOR")
    resp = await api_client.get("/api/admin/carreras", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_aislamiento_tenant_por_codigo(api_client) -> None:
    headers_a = await _auth_headers(api_client)
    resp_a = await api_client.post(
        "/api/admin/carreras",
        json={"codigo": "SHARED", "nombre": "Tenant A"},
        headers=headers_a,
    )
    assert resp_a.status_code == 201

    await _seed_tenant(
        tenant_id=TENANT_B,
        slug=SLUG_B,
        email="admin-b@estructura.test",
        role="ADMIN",
    )
    token_b = await _login(
        api_client,
        {"tenant_slug": SLUG_B, "email": "admin-b@estructura.test", "password": PW},
    )
    headers_b = {"Authorization": f"Bearer {token_b}"}
    resp_b = await api_client.post(
        "/api/admin/carreras",
        json={"codigo": "SHARED", "nombre": "Tenant B"},
        headers=headers_b,
    )
    assert resp_b.status_code == 201


@pytest.mark.asyncio
async def test_repository_no_ve_carreras_de_otro_tenant(session) -> None:
    factory = get_session_factory()
    async with factory() as db:
        db.add(Tenant(id=TENANT_A, nombre="A", slug=SLUG_A))
        db.add(Tenant(id=TENANT_B, nombre="B", slug=SLUG_B))
        await db.flush()
        from app.models.estructura import Carrera

        await CarreraRepository(db, TENANT_A).add(
            Carrera(codigo="X", nombre="Solo A")
        )
        await db.commit()

    async with factory() as db:
        found = await CarreraRepository(db, TENANT_B).get_by_codigo("X")
        assert found is None
