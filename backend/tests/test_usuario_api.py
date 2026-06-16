"""Tests API usuarios y asignaciones (C-07)."""

import uuid
from datetime import date

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c07")
SLUG = "c07-api"
EMAIL_ADMIN = "admin@c07.example.com"
EMAIL_COORD = "coord@c07.example.com"
EMAIL_PROF = "prof@c07.example.com"
PW = "S3cret!pass"


async def _seed_base(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C07 API", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        admin = await UsuarioRepository(session, TENANT_ID).add(
            Usuario(
                email=EMAIL_ADMIN,
                email_hash=email_blind_index(EMAIL_ADMIN),
                password_hash=hash_password(PW),
                nombre="Admin",
                apellidos="C07",
            )
        )
        coord = await UsuarioRepository(session, TENANT_ID).add(
            Usuario(
                email=EMAIL_COORD,
                email_hash=email_blind_index(EMAIL_COORD),
                password_hash=hash_password(PW),
                nombre="Coord",
                apellidos="C07",
            )
        )
        prof = await UsuarioRepository(session, TENANT_ID).add(
            Usuario(
                email=EMAIL_PROF,
                email_hash=email_blind_index(EMAIL_PROF),
                password_hash=hash_password(PW),
                nombre="Prof",
                apellidos="C07",
            )
        )
        for user, role in [(admin, "ADMIN"), (coord, "COORDINADOR"), (prof, "PROFESOR")]:
            rol = await RolRepository(session, TENANT_ID).get_by_codigo(role)
            assert rol is not None
            await UsuarioRolRepository(session, TENANT_ID).assign_role(user.id, rol.id)

        carrera = Carrera(
            tenant_id=TENANT_ID,
            codigo="TUP",
            nombre="Tecnicatura",
            estado=EntidadEstado.ACTIVA,
        )
        session.add(carrera)
        await session.flush()
        cohorte = Cohorte(
            tenant_id=TENANT_ID,
            carrera_id=carrera.id,
            nombre="2026-1",
            anio=2026,
            vig_desde=date(2026, 3, 1),
            estado=EntidadEstado.ACTIVA,
        )
        materia = Materia(
            tenant_id=TENANT_ID,
            codigo="PROG1",
            nombre="Programación I",
            estado=EntidadEstado.ACTIVA,
        )
        session.add_all([cohorte, materia])
        await session.flush()
        await session.commit()

    return {
        "tenant_slug": SLUG,
        "prof_id": str(prof.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "materia_id": str(materia.id),
    }


async def _login(api_client, email: str) -> str:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _headers(api_client, email: str) -> dict:
    token = await _login(api_client, email)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_usuario_crud_sin_pii_en_respuesta(api_client) -> None:
    ctx = await _seed_base(api_client)
    headers = await _headers(api_client, EMAIL_ADMIN)

    create = await api_client.post(
        "/api/admin/usuarios",
        json={
            "email": "nuevo@c07.example.com",
            "password": "Password1!",
            "nombre": "Nuevo",
            "apellidos": "Usuario",
        },
        headers=headers,
    )
    assert create.status_code == 201
    body = create.json()
    assert body["nombre"] == "Nuevo"
    assert "dni" not in body
    assert "cuil" not in body
    assert "email" not in body
    usuario_id = body["id"]

    listed = await api_client.get("/api/admin/usuarios", headers=headers)
    assert listed.status_code == 200
    assert any(u["id"] == usuario_id for u in listed.json()["items"])

    updated = await api_client.put(
        f"/api/admin/usuarios/{usuario_id}",
        json={"nombre": "Actualizado"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["nombre"] == "Actualizado"

    deleted = await api_client.delete(
        f"/api/admin/usuarios/{usuario_id}",
        headers=headers,
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_usuario_sin_permiso_403(api_client) -> None:
    await _seed_base(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.get("/api/admin/usuarios", headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_asignacion_crud(api_client) -> None:
    ctx = await _seed_base(api_client)
    headers = await _headers(api_client, EMAIL_COORD)

    payload = {
        "usuario_id": ctx["prof_id"],
        "rol": "PROFESOR",
        "materia_id": ctx["materia_id"],
        "carrera_id": ctx["carrera_id"],
        "cohorte_id": ctx["cohorte_id"],
        "comisiones": ["A"],
        "desde": "2026-03-01",
    }
    create = await api_client.post("/api/asignaciones", json=payload, headers=headers)
    assert create.status_code == 201
    asig = create.json()
    assert asig["vigente"] is True
    assert asig["rol"] == "PROFESOR"

    listed = await api_client.get(
        f"/api/asignaciones?materia_id={ctx['materia_id']}",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["items"]) == 1

    asig_id = asig["id"]
    updated = await api_client.put(
        f"/api/asignaciones/{asig_id}",
        json={"hasta": "2026-12-31"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["hasta"] == "2026-12-31"

    deleted = await api_client.delete(f"/api/asignaciones/{asig_id}", headers=headers)
    assert deleted.status_code == 204
