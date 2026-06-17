"""Tests API tareas — C-16."""

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

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c16")
SLUG = "c16-api"
EMAIL_COORD = "coord@c16.example.com"
EMAIL_PROF = "prof@c16.example.com"
EMAIL_TUTOR = "tutor@c16.example.com"
PW = "S3cret!pass"


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C16", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [
            (EMAIL_COORD, "COORDINADOR"),
            (EMAIL_PROF, "PROFESOR"),
            (EMAIL_TUTOR, "TUTOR"),
        ]:
            u = await UsuarioRepository(session, TENANT_ID).add(
                Usuario(
                    email=email,
                    email_hash=email_blind_index(email),
                    password_hash=hash_password(PW),
                )
            )
            rol = await RolRepository(session, TENANT_ID).get_by_codigo(role)
            assert rol is not None
            await UsuarioRolRepository(session, TENANT_ID).assign_role(u.id, rol.id)
            users[email] = u

        carrera = Carrera(
            tenant_id=TENANT_ID, codigo="TUP", nombre="TUP", estado=EntidadEstado.ACTIVA
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
        "materia_id": str(materia.id),
        "prof_id": str(users[EMAIL_PROF].id),
        "tutor_id": str(users[EMAIL_TUTOR].id),
        "coord_id": str(users[EMAIL_COORD].id),
    }


async def _headers(api_client, email: str = EMAIL_COORD) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_alta_y_mis_tareas(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/tareas",
        json={
            "asignado_a": ctx["prof_id"],
            "descripcion": "Revisar entregas pendientes",
            "materia_id": ctx["materia_id"],
        },
        headers=headers_coord,
    )
    assert resp.status_code == 201
    assert resp.json()["asignado_por"] == ctx["coord_id"]

    headers_prof = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.get("/api/tareas/mias", headers=headers_prof)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_delegacion_con_trazabilidad(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/tareas",
        json={"asignado_a": ctx["prof_id"], "descripcion": "Delegable"},
        headers=headers_coord,
    )
    tarea_id = resp.json()["id"]

    headers_prof = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.post(
        f"/api/tareas/{tarea_id}/delegar",
        json={"asignado_a": ctx["tutor_id"]},
        headers=headers_prof,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["asignado_a"] == ctx["tutor_id"]
    assert data["asignado_por"] == ctx["prof_id"]

    headers_tutor = await _headers(api_client, EMAIL_TUTOR)
    resp = await api_client.get("/api/tareas/mias", headers=headers_tutor)
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_transicion_estado_y_comentarios(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/tareas",
        json={"asignado_a": ctx["prof_id"], "descripcion": "Workflow"},
        headers=headers_coord,
    )
    tarea_id = resp.json()["id"]

    headers_prof = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.patch(
        f"/api/tareas/{tarea_id}/estado",
        json={"estado": "En progreso"},
        headers=headers_prof,
    )
    assert resp.status_code == 200

    await api_client.post(
        f"/api/tareas/{tarea_id}/comentarios",
        json={"texto": "Avance parcial"},
        headers=headers_prof,
    )
    resp = await api_client.patch(
        f"/api/tareas/{tarea_id}/estado",
        json={"estado": "Resuelta"},
        headers=headers_prof,
    )
    assert resp.status_code == 200

    resp = await api_client.get(
        f"/api/tareas/{tarea_id}/comentarios", headers=headers_prof
    )
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_admin_filtros(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    await api_client.post(
        "/api/tareas",
        json={"asignado_a": ctx["prof_id"], "descripcion": "Urgente materia X"},
        headers=headers_coord,
    )
    await api_client.post(
        "/api/tareas",
        json={"asignado_a": ctx["tutor_id"], "descripcion": "Otra cosa"},
        headers=headers_coord,
    )

    resp = await api_client.get(
        "/api/tareas/admin",
        params={"asignado_a": ctx["prof_id"], "busqueda": "Urgente"},
        headers=headers_coord,
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

    headers_prof = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.get("/api/tareas/admin", headers=headers_prof)
    assert resp.status_code == 403
