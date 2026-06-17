"""Tests API encuentros — C-13."""

import uuid
from datetime import date

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.encuentro import EstadoInstanciaEncuentro
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c13")
SLUG = "c13-api"
EMAIL_PROF = "prof@c13.example.com"
EMAIL_COORD = "coord@c13.example.com"
PW = "S3cret!pass"


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C13", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [
            (EMAIL_PROF, "PROFESOR"),
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
            usuario_id=users[EMAIL_PROF].id,
            rol=RolAsignacion.profesor,
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


async def _headers(api_client, email: str = EMAIL_PROF) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_recurrente_genera_instancias(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    resp = await api_client.post(
        "/api/encuentros/recurrente",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "Clase sync",
            "hora": "14:00:00",
            "dia_semana": "Lunes",
            "fecha_inicio": "2026-03-02",
            "cant_semanas": 3,
            "meet_url": "https://meet.example.com/abc",
            "vig_desde": "2026-03-02",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["instancias_generadas"] == 3

    lista = await api_client.get(
        "/api/encuentros/instancias",
        params={"materia_id": ctx["materia_id"]},
        headers=headers,
    )
    assert lista.status_code == 200
    assert len(lista.json()["items"]) == 3


@pytest.mark.asyncio
async def test_encuentro_unico(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    resp = await api_client.post(
        "/api/encuentros/unico",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "Consulta",
            "fecha": "2026-04-10",
            "hora": "10:00:00",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["titulo"] == "Consulta"


@pytest.mark.asyncio
async def test_editar_instancia_estado(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    creado = await api_client.post(
        "/api/encuentros/unico",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "TP oral",
            "fecha": "2026-04-15",
            "hora": "11:00:00",
        },
        headers=headers,
    )
    inst_id = creado.json()["id"]
    patch = await api_client.patch(
        f"/api/encuentros/instancias/{inst_id}",
        json={
            "estado": "Realizado",
            "video_url": "https://video.example.com/1",
            "comentario": "Bien",
        },
        headers=headers,
    )
    assert patch.status_code == 200
    assert patch.json()["estado"] == "Realizado"
    assert patch.json()["video_url"] == "https://video.example.com/1"


@pytest.mark.asyncio
async def test_html_aula_virtual(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await api_client.post(
        "/api/encuentros/unico",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "Cronograma",
            "fecha": "2026-05-01",
            "hora": "09:00:00",
        },
        headers=headers,
    )
    resp = await api_client.get(
        f"/api/encuentros/html/{ctx['materia_id']}",
        headers=headers,
    )
    assert resp.status_code == 200
    assert "Cronograma" in resp.json()["html"]


@pytest.mark.asyncio
async def test_admin_lista_tenant(api_client) -> None:
    ctx = await _seed(api_client)
    prof = await _headers(api_client, EMAIL_PROF)
    coord = await _headers(api_client, EMAIL_COORD)
    await api_client.post(
        "/api/encuentros/unico",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "Visible admin",
            "fecha": "2026-05-10",
            "hora": "15:00:00",
        },
        headers=prof,
    )
    resp = await api_client.get("/api/encuentros/admin", headers=coord)
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 1
