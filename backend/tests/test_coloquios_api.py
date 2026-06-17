"""Tests API coloquios — C-14."""

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

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c14")
SLUG = "c14-api"
EMAIL_COORD = "coord@c14.example.com"
EMAIL_ALUMNO = "alumno@c14.example.com"
EMAIL_ALUMNO2 = "alumno2@c14.example.com"
PW = "S3cret!pass"


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C14", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [
            (EMAIL_COORD, "COORDINADOR"),
            (EMAIL_ALUMNO, "ALUMNO"),
            (EMAIL_ALUMNO2, "ALUMNO"),
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
        "cohorte_id": str(cohorte.id),
        "alumno_id": str(users[EMAIL_ALUMNO].id),
        "alumno2_id": str(users[EMAIL_ALUMNO2].id),
    }


async def _headers(api_client, email: str = EMAIL_COORD) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_crear_convocatoria_y_metricas(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    resp = await api_client.post(
        "/api/coloquios/convocatorias",
        json={
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "instancia": "Coloquio Final",
            "turnos": [
                {"fecha": "2026-06-20", "hora": "10:00:00", "cupo_max": 2},
                {"fecha": "2026-06-21", "hora": "14:00:00", "cupo_max": 1},
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    eval_id = data["id"]
    assert len(data["turnos"]) == 2

    resp = await api_client.get("/api/coloquios/metricas", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["instancias_activas"] == 1

    resp = await api_client.get(f"/api/coloquios/convocatorias/{eval_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["convocados"] == 0
    assert resp.json()["cupos_libres"] == 3


@pytest.mark.asyncio
async def test_reserva_resta_cupo_y_rechaza_sin_cupo(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/coloquios/convocatorias",
        json={
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "instancia": "Coloquio Junio",
            "turnos": [{"fecha": "2026-06-22", "hora": "09:00:00", "cupo_max": 1}],
        },
        headers=headers_coord,
    )
    eval_id = resp.json()["id"]
    turno_id = resp.json()["turnos"][0]["id"]

    await api_client.post(
        f"/api/coloquios/convocatorias/{eval_id}/convocados",
        json={"alumno_ids": [ctx["alumno_id"], ctx["alumno2_id"]]},
        headers=headers_coord,
    )

    headers_a1 = await _headers(api_client, EMAIL_ALUMNO)
    resp = await api_client.post(
        f"/api/coloquios/convocatorias/{eval_id}/reservas",
        json={"turno_id": turno_id},
        headers=headers_a1,
    )
    assert resp.status_code == 201

    resp = await api_client.get(f"/api/coloquios/convocatorias/{eval_id}", headers=headers_coord)
    assert resp.json()["reservas_activas"] == 1
    assert resp.json()["cupos_libres"] == 0

    headers_a2 = await _headers(api_client, EMAIL_ALUMNO2)
    resp = await api_client.post(
        f"/api/coloquios/convocatorias/{eval_id}/reservas",
        json={"turno_id": turno_id},
        headers=headers_a2,
    )
    assert resp.status_code == 422
    assert "cupo" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_alumno_no_convocado_no_reserva(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/coloquios/convocatorias",
        json={
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "instancia": "Coloquio Julio",
            "turnos": [{"fecha": "2026-07-01", "hora": "11:00:00", "cupo_max": 5}],
        },
        headers=headers_coord,
    )
    eval_id = resp.json()["id"]
    turno_id = resp.json()["turnos"][0]["id"]

    headers_alumno = await _headers(api_client, EMAIL_ALUMNO)
    resp = await api_client.post(
        f"/api/coloquios/convocatorias/{eval_id}/reservas",
        json={"turno_id": turno_id},
        headers=headers_alumno,
    )
    assert resp.status_code == 422
    assert "convocado" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_resultado_consolidado(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/coloquios/convocatorias",
        json={
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "instancia": "Coloquio Notas",
            "turnos": [{"fecha": "2026-08-01", "hora": "15:00:00", "cupo_max": 3}],
        },
        headers=headers_coord,
    )
    eval_id = resp.json()["id"]
    await api_client.post(
        f"/api/coloquios/convocatorias/{eval_id}/convocados",
        json={"alumno_ids": [ctx["alumno_id"]]},
        headers=headers_coord,
    )
    resp = await api_client.post(
        f"/api/coloquios/convocatorias/{eval_id}/resultados",
        json={"alumno_id": ctx["alumno_id"], "nota_final": "8"},
        headers=headers_coord,
    )
    assert resp.status_code == 201

    resp = await api_client.get("/api/coloquios/resultados", headers=headers_coord)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["nota_final"] == "8"
