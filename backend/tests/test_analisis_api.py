"""Tests API análisis — C-11."""

import io
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

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c11")
SLUG = "c11-api"
EMAIL_PROF = "prof@c11.example.com"
EMAIL_COORD = "coord@c11.example.com"
EMAIL_ADMIN = "admin@c11.example.com"
PW = "S3cret!pass"

CSV_CALIF = b"""email,nombre,apellidos,TP1 (Real),Reflexion
ana@example.com,Ana,Garcia,75,Satisfactorio
pedro@example.com,Pedro,Lopez,45,No satisfactorio
"""

CSV_SOLO_NUM = b"""email,nombre,apellidos,TP1 (Real)
ana@example.com,Ana,Garcia,75
pedro@example.com,Pedro,Lopez,45
"""

PADRON_CSV = b"""nombre,apellidos,email,comision,regional
Ana,Garcia,ana@example.com,A,Norte
Pedro,Lopez,pedro@example.com,B,Sur
"""


async def _seed(api_client, *, comisiones: list[str] | None = None) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C11", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [
            (EMAIL_PROF, "PROFESOR"),
            (EMAIL_COORD, "COORDINADOR"),
            (EMAIL_ADMIN, "ADMIN"),
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
            comisiones=comisiones if comisiones is not None else [],
            desde=date(2026, 3, 1),
        )
        session.add(asig)
        await session.flush()
        await session.commit()

    return {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "asig_id": str(asig.id),
    }


async def _login(api_client, email: str = EMAIL_PROF) -> str:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _headers(api_client, email: str = EMAIL_PROF) -> dict:
    return {"Authorization": f"Bearer {await _login(api_client, email)}"}


async def _importar_padron(api_client, ctx: dict, headers: dict) -> None:
    resp = await api_client.post(
        "/api/padron/importar",
        data={"materia_id": ctx["materia_id"], "cohorte_id": ctx["cohorte_id"]},
        files={"file": ("padron.csv", io.BytesIO(PADRON_CSV), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 201


async def _importar_calif(
    api_client, ctx: dict, headers: dict, csv: bytes = CSV_CALIF
) -> None:
    resp = await api_client.post(
        "/api/calificaciones/importar",
        data={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "actividades": "TP1 (Real),Reflexion",
        },
        files={"file": ("notas.csv", io.BytesIO(csv), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_atrasados_rn06(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await _importar_calif(api_client, ctx, headers)

    resp = await api_client.get(
        "/api/analisis/atrasados",
        params={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_atrasados"] >= 1
    emails = {i["email"] for i in body["items"]}
    assert "pedro@example.com" in emails


@pytest.mark.asyncio
async def test_ranking_rn09(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await _importar_calif(api_client, ctx, headers)

    resp = await api_client.get(
        "/api/analisis/ranking",
        params={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    emails = [i["email"] for i in items]
    assert "ana@example.com" in emails
    assert "pedro@example.com" not in emails


@pytest.mark.asyncio
async def test_notas_finales_agrupadas(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await _importar_calif(api_client, ctx, headers)

    await api_client.put(
        "/api/analisis/agrupaciones",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "agrupaciones": [
                {"nombre": "Parcial 1", "actividades": ["TP1 (Real)"]},
            ],
        },
        headers=headers,
    )

    resp = await api_client.get(
        "/api/analisis/notas-finales",
        params={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    ana = next(
        i for i in resp.json()["items"] if i["email"] == "ana@example.com"
    )
    assert float(ana["grupos"]["Parcial 1"]) == 75.0


@pytest.mark.asyncio
async def test_monitor_filtro_comision(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await _importar_calif(api_client, ctx, headers)

    resp = await api_client.get(
        "/api/analisis/monitor/seguimiento",
        params={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "comision": "A",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["email"] == "ana@example.com"


@pytest.mark.asyncio
async def test_profesor_solo_ve_su_comision_en_analisis(api_client) -> None:
    """1.1 — PROFESOR con comisiones=['A'] no ve alumnos de comisión B."""
    ctx = await _seed(api_client, comisiones=["A"])
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await _importar_calif(api_client, ctx, headers)

    params = {
        "asignacion_id": ctx["asig_id"],
        "materia_id": ctx["materia_id"],
        "cohorte_id": ctx["cohorte_id"],
    }

    atrasados = await api_client.get(
        "/api/analisis/atrasados", params=params, headers=headers
    )
    assert atrasados.status_code == 200
    body = atrasados.json()
    assert body["total_alumnos"] == 1
    emails_atrasados = {i["email"] for i in body["items"]}
    assert "pedro@example.com" not in emails_atrasados

    ranking = await api_client.get(
        "/api/analisis/ranking", params=params, headers=headers
    )
    assert ranking.status_code == 200
    emails_ranking = {i["email"] for i in ranking.json()["items"]}
    assert "ana@example.com" in emails_ranking
    assert "pedro@example.com" not in emails_ranking

    await api_client.put(
        "/api/analisis/agrupaciones",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "agrupaciones": [{"nombre": "Parcial 1", "actividades": ["TP1 (Real)"]}],
        },
        headers=headers,
    )
    notas = await api_client.get(
        "/api/analisis/notas-finales", params=params, headers=headers
    )
    assert notas.status_code == 200
    emails_notas = {i["email"] for i in notas.json()["items"]}
    assert emails_notas == {"ana@example.com"}

    sin_corregir = await api_client.get(
        "/api/analisis/sin-corregir", params=params, headers=headers
    )
    assert sin_corregir.status_code == 200
    emails_sc = {i["email"] for i in sin_corregir.json()["items"]}
    assert "pedro@example.com" not in emails_sc


@pytest.mark.asyncio
async def test_profesor_comisiones_vacio_ve_todo(api_client) -> None:
    """1.2 — comisiones=[] retrocompatible: ve todas las comisiones."""
    ctx = await _seed(api_client, comisiones=[])
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await _importar_calif(api_client, ctx, headers)

    resp = await api_client.get(
        "/api/analisis/atrasados",
        params={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total_alumnos"] == 2


@pytest.mark.asyncio
async def test_coordinador_ve_todas_las_comisiones(api_client) -> None:
    """1.3 — COORDINADOR sin restricción por comisión de la asignación."""
    ctx = await _seed(api_client, comisiones=["A"])
    headers_prof = await _headers(api_client)
    headers_coord = await _headers(api_client, EMAIL_COORD)
    await _importar_padron(api_client, ctx, headers_prof)
    await _importar_calif(api_client, ctx, headers_prof)

    params = {
        "asignacion_id": ctx["asig_id"],
        "materia_id": ctx["materia_id"],
        "cohorte_id": ctx["cohorte_id"],
    }
    resp = await api_client.get(
        "/api/analisis/atrasados", params=params, headers=headers_coord
    )
    assert resp.status_code == 200
    assert resp.json()["total_alumnos"] == 2
    emails = {i["email"] for i in resp.json()["items"]}
    assert "pedro@example.com" in emails


@pytest.mark.asyncio
async def test_entrada_sin_comision_no_visible_para_profesor(api_client) -> None:
    """5.2 — comision=null solo visible para roles amplios, no PROFESOR restringido."""
    ctx = await _seed(api_client, comisiones=["A"])
    headers_prof = await _headers(api_client)
    headers_coord = await _headers(api_client, EMAIL_COORD)

    padron_sin_comision = b"""nombre,apellidos,email,comision,regional
Luis,Martinez,luis@example.com,,Norte
Ana,Garcia,ana@example.com,A,Norte
"""
    await api_client.post(
        "/api/padron/importar",
        data={"materia_id": ctx["materia_id"], "cohorte_id": ctx["cohorte_id"]},
        files={"file": ("padron.csv", io.BytesIO(padron_sin_comision), "text/csv")},
        headers=headers_coord,
    )

    params = {
        "asignacion_id": ctx["asig_id"],
        "materia_id": ctx["materia_id"],
        "cohorte_id": ctx["cohorte_id"],
    }
    prof_resp = await api_client.get(
        "/api/analisis/atrasados", params=params, headers=headers_prof
    )
    prof_emails = {i["email"] for i in prof_resp.json()["items"]}
    assert "luis@example.com" not in prof_emails

    coord_resp = await api_client.get(
        "/api/analisis/atrasados", params=params, headers=headers_coord
    )
    assert coord_resp.json()["total_alumnos"] == 2


@pytest.mark.asyncio
async def test_sin_corregir_export_textual(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)
    await api_client.put(
        "/api/analisis/agrupaciones",
        json={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "agrupaciones": [
                {"nombre": "Textuales", "actividades": ["Reflexion"]},
            ],
        },
        headers=headers,
    )
    await api_client.post(
        "/api/calificaciones/importar",
        data={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "actividades": "TP1 (Real)",
        },
        files={"file": ("notas.csv", io.BytesIO(CSV_SOLO_NUM), "text/csv")},
        headers=headers,
    )

    resp = await api_client.get(
        "/api/analisis/sin-corregir/export",
        params={
            "asignacion_id": ctx["asig_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert b"Reflexion" in resp.content
