"""Tests API calificaciones — C-10."""

import io
import uuid
from datetime import date

import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.calificacion_repository import CalificacionRepository
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c10")
SLUG = "c10-api"
EMAIL_PROF = "prof@c10.example.com"
EMAIL_PROF2 = "prof2@c10.example.com"
PW = "S3cret!pass"

CSV_CALIF = b"""email,nombre,apellidos,TP1 (Real),Reflexion
ana@example.com,Ana,Garcia,75,Satisfactorio
pedro@example.com,Pedro,Lopez,45,No satisfactorio
"""

CSV_FINALIZACION = b"""email,actividad,estado
ana@example.com,Reflexion,completado
pedro@example.com,Reflexion,completado
"""

PADRON_CSV = b"""nombre,apellidos,email,comision
Ana,Garcia,ana@example.com,A
Pedro,Lopez,pedro@example.com,B
"""


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C10", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        profs: dict[str, Usuario] = {}
        for email, role in [(EMAIL_PROF, "PROFESOR"), (EMAIL_PROF2, "PROFESOR")]:
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
            profs[email] = u

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

        asig1 = Asignacion(
            tenant_id=TENANT_ID,
            usuario_id=profs[EMAIL_PROF].id,
            rol=RolAsignacion.profesor,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            desde=date(2026, 3, 1),
        )
        asig2 = Asignacion(
            tenant_id=TENANT_ID,
            usuario_id=profs[EMAIL_PROF2].id,
            rol=RolAsignacion.profesor,
            materia_id=materia.id,
            carrera_id=carrera.id,
            cohorte_id=cohorte.id,
            desde=date(2026, 3, 1),
        )
        session.add_all([asig1, asig2])
        await session.flush()
        await session.commit()

    return {
        "tenant_slug": SLUG,
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "asig1_id": str(asig1.id),
        "asig2_id": str(asig2.id),
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


@pytest.mark.asyncio
async def test_preview_calificaciones(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client)
    resp = await api_client.post(
        "/api/calificaciones/preview",
        files={"file": ("notas.csv", io.BytesIO(CSV_CALIF), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_filas"] == 2
    tipos = {a["tipo"] for a in body["actividades"]}
    assert "numerica" in tipos
    assert "textual" in tipos


@pytest.mark.asyncio
async def test_importar_y_aprobado_derivado(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)

    resp = await api_client.post(
        "/api/calificaciones/importar",
        data={
            "asignacion_id": ctx["asig1_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "actividades": "TP1 (Real),Reflexion",
        },
        files={"file": ("notas.csv", io.BytesIO(CSV_CALIF), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 201
    items = resp.json()["items"]
    assert resp.json()["importadas"] >= 2
    por_actividad = {(i["actividad"], i["aprobado"]) for i in items}
    assert ("TP1 (Real)", True) in por_actividad or any(
        i["actividad"] == "TP1 (Real)" and i["aprobado"] for i in items
    )


@pytest.mark.asyncio
async def test_umbral_no_afecta_otro_docente(api_client, session) -> None:
    ctx = await _seed(api_client)
    headers1 = await _headers(api_client, EMAIL_PROF)
    headers2 = await _headers(api_client, EMAIL_PROF2)
    await _importar_padron(api_client, ctx, headers1)

    for headers, asig in [(headers1, ctx["asig1_id"]), (headers2, ctx["asig2_id"])]:
        await api_client.post(
            "/api/calificaciones/importar",
            data={
                "asignacion_id": asig,
                "materia_id": ctx["materia_id"],
                "cohorte_id": ctx["cohorte_id"],
                "actividades": "TP1 (Real)",
            },
            files={"file": ("notas.csv", io.BytesIO(CSV_CALIF), "text/csv")},
            headers=headers,
        )

    await api_client.put(
        "/api/calificaciones/umbral",
        json={
            "asignacion_id": ctx["asig1_id"],
            "materia_id": ctx["materia_id"],
            "umbral_pct": 80,
        },
        headers=headers1,
    )

    repo = CalificacionRepository(session, TENANT_ID)
    c1 = [c for c in await repo.list_by_asignacion(uuid.UUID(ctx["asig1_id"])) if c.actividad == "TP1 (Real)"]
    c2 = [c for c in await repo.list_by_asignacion(uuid.UUID(ctx["asig2_id"])) if c.actividad == "TP1 (Real)"]
    ana1 = next(c for c in c1 if c.nota_numerica == 75)
    ana2 = next(c for c in c2 if c.nota_numerica == 75)
    assert ana1.aprobado is False  # umbral 80
    assert ana2.aprobado is True   # umbral default 60


@pytest.mark.asyncio
async def test_finalizacion_sin_corregir(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client)
    await _importar_padron(api_client, ctx, headers)

    await api_client.post(
        "/api/calificaciones/importar",
        data={
            "asignacion_id": ctx["asig1_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "actividades": "TP1 (Real)",
        },
        files={"file": ("notas.csv", io.BytesIO(CSV_CALIF), "text/csv")},
        headers=headers,
    )

    resp = await api_client.post(
        "/api/calificaciones/finalizacion/preview",
        data={
            "asignacion_id": ctx["asig1_id"],
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
        },
        files={"file": ("fin.csv", io.BytesIO(CSV_FINALIZACION), "text/csv")},
        headers=headers,
    )
    assert resp.status_code == 200
    emails = {i["email"] for i in resp.json()["items"]}
    assert "pedro@example.com" in emails
