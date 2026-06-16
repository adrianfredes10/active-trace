"""Tests API equipos docentes (C-08)."""

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

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c08")
SLUG = "c08-api"
EMAIL_COORD = "coord@c08.example.com"
EMAIL_PROF = "prof@c08.example.com"
EMAIL_TUTOR = "tutor@c08.example.com"
PW = "S3cret!pass"


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C08", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role, nombre in [
            (EMAIL_COORD, "COORDINADOR", "Coord"),
            (EMAIL_PROF, "PROFESOR", "Prof"),
            (EMAIL_TUTOR, "TUTOR", "Tutor"),
        ]:
            u = await UsuarioRepository(session, TENANT_ID).add(
                Usuario(
                    email=email,
                    email_hash=email_blind_index(email),
                    password_hash=hash_password(PW),
                    nombre=nombre,
                    apellidos="C08",
                )
            )
            rol = await RolRepository(session, TENANT_ID).get_by_codigo(role)
            assert rol is not None
            await UsuarioRolRepository(session, TENANT_ID).assign_role(u.id, rol.id)
            users[role] = u

        carrera = Carrera(
            tenant_id=TENANT_ID, codigo="TUP", nombre="TUP", estado=EntidadEstado.ACTIVA
        )
        session.add(carrera)
        await session.flush()
        cohorte_origen = Cohorte(
            tenant_id=TENANT_ID,
            carrera_id=carrera.id,
            nombre="2025-2",
            anio=2025,
            vig_desde=date(2025, 8, 1),
            estado=EntidadEstado.ACTIVA,
        )
        cohorte_destino = Cohorte(
            tenant_id=TENANT_ID,
            carrera_id=carrera.id,
            nombre="2026-1",
            anio=2026,
            vig_desde=date(2026, 3, 1),
            estado=EntidadEstado.ACTIVA,
        )
        materia = Materia(
            tenant_id=TENANT_ID,
            codigo="BD1",
            nombre="Bases de Datos",
            estado=EntidadEstado.ACTIVA,
        )
        session.add_all([cohorte_origen, cohorte_destino, materia])
        await session.flush()

        session.add(
            Asignacion(
                tenant_id=TENANT_ID,
                usuario_id=users["PROFESOR"].id,
                rol=RolAsignacion.profesor,
                materia_id=materia.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte_origen.id,
                comisiones=["A"],
                desde=date(2025, 8, 1),
            )
        )
        await session.commit()

    return {
        "tenant_slug": SLUG,
        "prof_id": str(users["PROFESOR"].id),
        "tutor_id": str(users["TUTOR"].id),
        "carrera_id": str(carrera.id),
        "cohorte_origen_id": str(cohorte_origen.id),
        "cohorte_destino_id": str(cohorte_destino.id),
        "materia_id": str(materia.id),
    }


async def _login(api_client, email: str) -> str:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _headers(api_client, email: str) -> dict:
    return {"Authorization": f"Bearer {await _login(api_client, email)}"}


@pytest.mark.asyncio
async def test_mis_equipos_desde_sesion(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.get("/api/equipos/mis-equipos", headers=headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["rol"] == "PROFESOR"
    assert items[0]["materia_id"] == ctx["materia_id"]


@pytest.mark.asyncio
async def test_asignacion_masiva(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_COORD)
    resp = await api_client.post(
        "/api/equipos/asignacion-masiva",
        json={
            "usuario_ids": [ctx["tutor_id"]],
            "rol": "TUTOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_origen_id"],
            "desde": "2026-03-01",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["creadas"] == 1


@pytest.mark.asyncio
async def test_clonar_equipo_entre_cohortes(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_COORD)
    resp = await api_client.post(
        "/api/equipos/clonar",
        json={
            "origen": {
                "materia_id": ctx["materia_id"],
                "carrera_id": ctx["carrera_id"],
                "cohorte_id": ctx["cohorte_origen_id"],
            },
            "destino": {
                "materia_id": ctx["materia_id"],
                "carrera_id": ctx["carrera_id"],
                "cohorte_id": ctx["cohorte_destino_id"],
            },
            "desde": "2026-03-01",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["creadas"] == 1
    clon = resp.json()["items"][0]
    assert clon["cohorte_id"] == ctx["cohorte_destino_id"]


@pytest.mark.asyncio
async def test_modificar_vigencia_equipo(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_COORD)
    resp = await api_client.patch(
        "/api/equipos/vigencia",
        json={
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_origen_id"],
            "desde": "2025-08-01",
            "hasta": "2025-12-15",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["actualizadas"] >= 1
    assert resp.json()["items"][0]["hasta"] == "2025-12-15"


@pytest.mark.asyncio
async def test_exportar_equipo_csv(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_COORD)
    resp = await api_client.get(
        "/api/equipos/exportar",
        params={
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_origen_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert "usuario_id" in resp.text
    assert "PROFESOR" in resp.text
