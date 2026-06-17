"""Tests API programas y fechas académicas — C-17."""

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

TENANT_A = uuid.UUID("00000000-0000-0000-0000-000000000c17")
TENANT_B = uuid.UUID("00000000-0000-0000-0000-000000000b17")
SLUG_A = "c17-api"
SLUG_B = "c17-b"
EMAIL_ADMIN = "admin@c17.example.com"
PW = "S3cret!pass"


async def _seed_tenant(tenant_id: uuid.UUID, slug: str) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=tenant_id, nombre=slug, slug=slug))
        await session.flush()
        await seed_tenant_rbac(session, tenant_id)

        admin = await UsuarioRepository(session, tenant_id).add(
            Usuario(
                email=f"admin@{slug}.example.com",
                email_hash=email_blind_index(f"admin@{slug}.example.com"),
                password_hash=hash_password(PW),
            )
        )
        rol = await RolRepository(session, tenant_id).get_by_codigo("ADMIN")
        assert rol is not None
        await UsuarioRolRepository(session, tenant_id).assign_role(admin.id, rol.id)

        carrera = Carrera(
            tenant_id=tenant_id,
            codigo="TUP",
            nombre="TUP",
            estado=EntidadEstado.ACTIVA,
        )
        session.add(carrera)
        await session.flush()
        cohorte = Cohorte(
            tenant_id=tenant_id,
            carrera_id=carrera.id,
            nombre="2026-1",
            anio=2026,
            vig_desde=date(2026, 3, 1),
            estado=EntidadEstado.ACTIVA,
        )
        materia = Materia(
            tenant_id=tenant_id,
            codigo="PROG1",
            nombre="Programación I",
            estado=EntidadEstado.ACTIVA,
        )
        session.add_all([cohorte, materia])
        await session.flush()
        await session.commit()

    return {
        "materia_id": str(materia.id),
        "carrera_id": str(carrera.id),
        "cohorte_id": str(cohorte.id),
    }


async def _headers(api_client, slug: str, email: str) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": slug, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_programa_asociacion_y_referencia_opaca(api_client) -> None:
    ctx = await _seed_tenant(TENANT_A, SLUG_A)
    headers = await _headers(api_client, SLUG_A, f"admin@{SLUG_A}.example.com")
    resp = await api_client.post(
        "/api/programas",
        json={
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "titulo": "Programa 2026",
            "nombre_archivo": "prog1.pdf",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    ref = resp.json()["referencia_archivo"]
    assert ref.startswith(f"ref:{TENANT_A}:")
    assert "prog1.pdf" in ref

    resp = await api_client.get(
        "/api/programas",
        params={"materia_id": ctx["materia_id"]},
        headers=headers,
    )
    assert len(resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_fechas_crud_calendario_y_html(api_client) -> None:
    ctx = await _seed_tenant(TENANT_A, SLUG_A)
    headers = await _headers(api_client, SLUG_A, f"admin@{SLUG_A}.example.com")
    resp = await api_client.post(
        "/api/fechas-academicas",
        json={
            "materia_id": ctx["materia_id"],
            "cohorte_id": ctx["cohorte_id"],
            "tipo": "Parcial",
            "numero": 1,
            "periodo": "2026-1",
            "fecha": "2026-06-20",
            "titulo": "Primer parcial",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    fecha_id = resp.json()["id"]

    resp = await api_client.get(
        "/api/fechas-academicas/calendario",
        params={"desde": "2026-06-01", "hasta": "2026-06-30"},
        headers=headers,
    )
    assert len(resp.json()["items"]) == 1

    resp = await api_client.get(
        f"/api/fechas-academicas/html/{ctx['materia_id']}",
        params={"cohorte_id": ctx["cohorte_id"]},
        headers=headers,
    )
    assert "Cronograma" in resp.json()["html"]

    resp = await api_client.patch(
        f"/api/fechas-academicas/{fecha_id}",
        json={"titulo": "Parcial actualizado"},
        headers=headers,
    )
    assert resp.json()["titulo"] == "Parcial actualizado"


@pytest.mark.asyncio
async def test_aislamiento_tenant_programas(api_client) -> None:
    ctx_a = await _seed_tenant(TENANT_A, SLUG_A)
    await _seed_tenant(TENANT_B, SLUG_B)
    headers_a = await _headers(api_client, SLUG_A, f"admin@{SLUG_A}.example.com")
    await api_client.post(
        "/api/programas",
        json={
            "materia_id": ctx_a["materia_id"],
            "carrera_id": ctx_a["carrera_id"],
            "cohorte_id": ctx_a["cohorte_id"],
            "titulo": "Solo tenant A",
            "nombre_archivo": "a.pdf",
        },
        headers=headers_a,
    )
    headers_b = await _headers(api_client, SLUG_B, f"admin@{SLUG_B}.example.com")
    resp = await api_client.get("/api/programas", headers=headers_b)
    assert resp.json()["items"] == []
