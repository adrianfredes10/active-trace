"""Tests API guardias — C-13."""

import uuid
from datetime import date

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c31")
SLUG = "c13g-api"
EMAIL_TUTOR = "tutor@c13.example.com"
EMAIL_COORD = "coord@c13.example.com"
PW = "S3cret!pass"


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C13G", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [
            (EMAIL_TUTOR, "TUTOR"),
            (EMAIL_COORD, "COORDINADOR"),
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

        asig = Asignacion(
            tenant_id=TENANT_ID,
            usuario_id=users[EMAIL_TUTOR].id,
            rol=RolAsignacion.tutor,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            desde=date(2026, 3, 1),
        )
        session.add(asig)
        await session.flush()
        await session.commit()

    return {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "carrera_id": str(carrera.id),
        "asig_id": str(asig.id),
    }


async def _headers(api_client, email: str) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_registrar_guardia(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_TUTOR)
    resp = await api_client.post(
        "/api/guardias",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Miércoles",
            "horario": "14:00-14:45",
            "comentarios": "Guardia semanal",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_export_guardias_coord(api_client) -> None:
    ctx = await _seed(api_client)
    tutor = await _headers(api_client, EMAIL_TUTOR)
    coord = await _headers(api_client, EMAIL_COORD)
    await api_client.post(
        "/api/guardias",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Viernes",
            "horario": "10:00-10:45",
        },
        headers=tutor,
    )
    resp = await api_client.get("/api/guardias/export", headers=coord)
    assert resp.status_code == 200
    assert b"Viernes" in resp.content
