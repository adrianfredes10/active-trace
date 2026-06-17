"""Tests API avisos — C-15."""

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c15")
SLUG = "c15-api"
EMAIL_COORD = "coord@c15.example.com"
EMAIL_ALUMNO = "alumno@c15.example.com"
PW = "S3cret!pass"
NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C15", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [(EMAIL_COORD, "COORDINADOR"), (EMAIL_ALUMNO, "ALUMNO")]:
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
            usuario_id=users[EMAIL_ALUMNO].id,
            rol=RolAsignacion.alumno,
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
    }


async def _headers(api_client, email: str = EMAIL_COORD) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_aviso_por_cohorte_visible_y_fuera_vigencia_no(api_client, monkeypatch) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)

    inicio = NOW - timedelta(days=1)
    fin = NOW + timedelta(days=7)
    resp = await api_client.post(
        "/api/avisos",
        json={
            "alcance": "PorCohorte",
            "cohorte_id": ctx["cohorte_id"],
            "titulo": "Inicio cuatrimestre",
            "cuerpo": "Bienvenidos",
            "inicio_en": _iso(inicio),
            "fin_en": _iso(fin),
            "orden": 10,
            "requiere_ack": False,
        },
        headers=headers_coord,
    )
    assert resp.status_code == 201

    headers_alumno = await _headers(api_client, EMAIL_ALUMNO)
    resp = await api_client.get("/api/avisos/mios", headers=headers_alumno)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1

    resp = await api_client.post(
        "/api/avisos",
        json={
            "alcance": "Global",
            "titulo": "Futuro",
            "cuerpo": "Aún no",
            "inicio_en": _iso(NOW + timedelta(days=30)),
            "fin_en": _iso(NOW + timedelta(days=60)),
        },
        headers=headers_coord,
    )
    assert resp.status_code == 201
    resp = await api_client.get("/api/avisos/mios", headers=headers_alumno)
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_ack_oculta_aviso_y_cuenta_metricas(api_client) -> None:
    ctx = await _seed(api_client)
    headers_coord = await _headers(api_client)
    resp = await api_client.post(
        "/api/avisos",
        json={
            "alcance": "PorMateria",
            "materia_id": ctx["materia_id"],
            "titulo": "Leer obligatorio",
            "cuerpo": "Confirmar lectura",
            "inicio_en": _iso(NOW - timedelta(hours=1)),
            "requiere_ack": True,
            "orden": 100,
        },
        headers=headers_coord,
    )
    aviso_id = resp.json()["id"]

    headers_alumno = await _headers(api_client, EMAIL_ALUMNO)
    resp = await api_client.get("/api/avisos/mios", headers=headers_alumno)
    assert len(resp.json()["items"]) == 1

    resp = await api_client.post(f"/api/avisos/{aviso_id}/ack", headers=headers_alumno)
    assert resp.status_code == 201

    resp = await api_client.get("/api/avisos/mios", headers=headers_alumno)
    assert len(resp.json()["items"]) == 0

    resp = await api_client.get(f"/api/avisos/{aviso_id}/metricas", headers=headers_coord)
    assert resp.status_code == 200
    assert resp.json()["confirmaciones"] == 1


@pytest.mark.asyncio
async def test_orden_prioridad(api_client) -> None:
    await _seed(api_client)
    headers_coord = await _headers(api_client)
    inicio = _iso(NOW - timedelta(days=1))
    for orden, titulo in [(1, "Bajo"), (50, "Alto")]:
        await api_client.post(
            "/api/avisos",
            json={
                "alcance": "Global",
                "titulo": titulo,
                "cuerpo": "x",
                "inicio_en": inicio,
                "orden": orden,
            },
            headers=headers_coord,
        )
    headers_alumno = await _headers(api_client, EMAIL_ALUMNO)
    resp = await api_client.get("/api/avisos/mios", headers=headers_alumno)
    titulos = [i["titulo"] for i in resp.json()["items"]]
    assert titulos[0] == "Alto"
