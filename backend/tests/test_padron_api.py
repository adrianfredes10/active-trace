"""Tests API padrón — C-09."""

import io
import uuid
from datetime import date
from unittest.mock import AsyncMock, patch

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.integrations.moodle_ws import MoodleUnavailable
from app.models import Tenant, Usuario
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.padron_repository import VersionPadronRepository
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.padron_parser import parse_csv
from app.services.padron_service import PadronService
from app.services.rbac_seed import seed_tenant_rbac

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c09")
SLUG = "c09-api"
EMAIL_COORD = "coord@c09.example.com"
PW = "S3cret!pass"

CSV_SAMPLE = b"""nombre,apellidos,email,comision
Ana,Garcia,ana@example.com,A
Pedro,Lopez,pedro@example.com,B
"""


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C09", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)
        coord = await UsuarioRepository(session, TENANT_ID).add(
            Usuario(
                email=EMAIL_COORD,
                email_hash=email_blind_index(EMAIL_COORD),
                password_hash=hash_password(PW),
            )
        )
        rol = await RolRepository(session, TENANT_ID).get_by_codigo("COORDINADOR")
        assert rol is not None
        await UsuarioRolRepository(session, TENANT_ID).assign_role(coord.id, rol.id)

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
        "tenant_slug": SLUG,
        "coord_id": str(coord.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
        "materia_id": str(materia.id),
    }


async def _login(api_client) -> str:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": EMAIL_COORD, "password": PW},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _headers(api_client) -> dict:
    return {"Authorization": f"Bearer {await _login(api_client)}"}


def test_parse_csv_ok() -> None:
    filas = parse_csv(CSV_SAMPLE)
    assert len(filas) == 2
    assert filas[0].email == "ana@example.com"


@pytest.mark.asyncio
async def test_preview_padron(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client)
    resp = await api_client.post(
        "/api/padron/preview",
        files={"file": ("padron.csv", io.BytesIO(CSV_SAMPLE), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 2
    assert "email" in resp.json()["filas"][0]


@pytest.mark.asyncio
async def test_importar_padron_y_versionado(api_client, session) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)

    resp1 = await api_client.post(
        "/api/padron/importar",
        data={"materia_id": ctx["materia_id"], "cohorte_id": ctx["cohorte_id"]},
        files={"file": ("padron.csv", io.BytesIO(CSV_SAMPLE), "text/csv")},
        headers=headers,
    )
    assert resp1.status_code == 201
    v1 = resp1.json()["version"]["id"]
    assert resp1.json()["version"]["activa"] is True
    assert len(resp1.json()["entradas"]) == 2
    assert resp1.json()["entradas"][0]["usuario_id"] is None

    csv2 = b"nombre,apellidos,email\nLuis,Martinez,luis@example.com\n"
    resp2 = await api_client.post(
        "/api/padron/importar",
        data={"materia_id": ctx["materia_id"], "cohorte_id": ctx["cohorte_id"]},
        files={"file": ("padron.csv", io.BytesIO(csv2), "text/csv")},
        headers=headers,
    )
    assert resp2.status_code == 201
    v2 = resp2.json()["version"]["id"]
    assert v2 != v1

    repo = VersionPadronRepository(session, TENANT_ID)
    activa = await repo.get_activa(uuid.UUID(ctx["materia_id"]), uuid.UUID(ctx["cohorte_id"]))
    assert activa is not None
    assert str(activa.id) == v2


@pytest.mark.asyncio
async def test_vaciar_padron_scope_usuario(api_client, session) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await api_client.post(
        "/api/padron/importar",
        data={"materia_id": ctx["materia_id"], "cohorte_id": ctx["cohorte_id"]},
        files={"file": ("padron.csv", io.BytesIO(CSV_SAMPLE), "text/csv")},
        headers=headers,
    )

    vaciar = await api_client.delete(
        f"/api/padron/materias/{ctx['materia_id']}/datos",
        headers=headers,
    )
    assert vaciar.status_code == 200
    assert vaciar.json()["versiones_eliminadas"] >= 1

    svc = PadronService(session, TENANT_ID)
    activa = await svc.get_version_activa(
        uuid.UUID(ctx["materia_id"]), uuid.UUID(ctx["cohorte_id"])
    )
    assert activa is None


@pytest.mark.asyncio
async def test_moodle_sync_502(api_client, monkeypatch) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)

    monkeypatch.setenv("MOODLE_BASE_URL", "http://moodle.test")
    monkeypatch.setenv("MOODLE_TOKEN", "token")
    from app.core.config import get_settings

    get_settings.cache_clear()

    with patch(
        "app.integrations.moodle_ws.MoodleWSClient.fetch_participants",
        new_callable=AsyncMock,
        side_effect=MoodleUnavailable("timeout"),
    ):
        resp = await api_client.post(
            "/api/padron/moodle/sync",
            json={
                "materia_id": ctx["materia_id"],
                "cohorte_id": ctx["cohorte_id"],
                "moodle_course_id": 42,
            },
            headers=headers,
        )
    assert resp.status_code == 502
