"""Tests API panel de auditoría — C-19."""

import uuid
from datetime import date, datetime, timezone

import pytest

from app.core.audit_actions import AuditAction
from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import AuditLog, Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c19")
SLUG = "c19-api"
EMAIL_ADMIN = "admin@c19.example.com"
EMAIL_COORD1 = "coord1@c19.example.com"
EMAIL_COORD2 = "coord2@c19.example.com"
EMAIL_PROF = "prof@c19.example.com"
PW = "S3cret!pass"
NOW = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C19", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role in [
            (EMAIL_ADMIN, "ADMIN"),
            (EMAIL_COORD1, "COORDINADOR"),
            (EMAIL_COORD2, "COORDINADOR"),
            (EMAIL_PROF, "PROFESOR"),
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
        m1 = Materia(
            tenant_id=TENANT_ID, codigo="M1", nombre="Mat 1", estado=EntidadEstado.ACTIVA
        )
        m2 = Materia(
            tenant_id=TENANT_ID, codigo="M2", nombre="Mat 2", estado=EntidadEstado.ACTIVA
        )
        session.add_all([cohorte, m1, m2])
        await session.flush()

        session.add(
            Asignacion(
                tenant_id=TENANT_ID,
                usuario_id=users[EMAIL_COORD1].id,
                rol=RolAsignacion.coordinador,
                materia_id=m1.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                desde=date(2026, 3, 1),
            )
        )
        session.add(
            Asignacion(
                tenant_id=TENANT_ID,
                usuario_id=users[EMAIL_COORD2].id,
                rol=RolAsignacion.coordinador,
                materia_id=m2.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                desde=date(2026, 3, 1),
            )
        )
        session.add(
            Asignacion(
                tenant_id=TENANT_ID,
                usuario_id=users[EMAIL_PROF].id,
                rol=RolAsignacion.profesor,
                materia_id=m1.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                desde=date(2026, 3, 1),
            )
        )

        session.add_all(
            [
                AuditLog(
                    tenant_id=TENANT_ID,
                    fecha_hora=NOW,
                    actor_id=users[EMAIL_PROF].id,
                    materia_id=m1.id,
                    accion=AuditAction.CALIFICACIONES_IMPORTAR,
                    filas_afectadas=10,
                ),
                AuditLog(
                    tenant_id=TENANT_ID,
                    fecha_hora=NOW,
                    actor_id=users[EMAIL_PROF].id,
                    materia_id=m2.id,
                    accion=AuditAction.PADRON_CARGAR,
                    filas_afectadas=5,
                ),
            ]
        )
        lote = uuid.uuid4()
        session.add(
            Comunicacion(
                tenant_id=TENANT_ID,
                enviado_por=users[EMAIL_PROF].id,
                materia_id=m1.id,
                destinatario="alumno@test.com",
                asunto="Aviso",
                cuerpo="Hola",
                estado=EstadoComunicacion.pendiente,
                lote_id=lote,
                es_masivo=False,
                aprobado=True,
            )
        )
        await session.flush()
        await session.commit()

    return {"m1_id": str(m1.id), "m2_id": str(m2.id), "prof_id": str(users[EMAIL_PROF].id)}


async def _headers(api_client, email: str) -> dict:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.mark.asyncio
async def test_acciones_por_dia_y_limite_log(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client, EMAIL_ADMIN)
    resp = await api_client.get(
        "/api/auditoria/panel/acciones-por-dia",
        params={
            "desde": NOW.replace(hour=0).isoformat(),
            "hasta": NOW.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 2

    resp = await api_client.get("/api/auditoria/log", params={"limit": 200}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["limit"] == 200
    assert len(resp.json()["items"]) == 2


@pytest.mark.asyncio
async def test_comunicaciones_por_docente(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client, EMAIL_ADMIN)
    resp = await api_client.get(
        "/api/auditoria/panel/comunicaciones-por-docente", headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["items"][0]["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_scope_propio_coordinador(api_client) -> None:
    ctx = await _seed(api_client)
    headers_c1 = await _headers(api_client, EMAIL_COORD1)
    resp = await api_client.get(
        "/api/auditoria/log",
        params={"materia_id": ctx["m1_id"]},
        headers=headers_c1,
    )
    assert len(resp.json()["items"]) == 1
    assert resp.json()["items"][0]["accion"] == "CALIFICACIONES_IMPORTAR"

    resp = await api_client.get(
        "/api/auditoria/log",
        params={"materia_id": ctx["m2_id"]},
        headers=headers_c1,
    )
    assert resp.json()["items"] == []


@pytest.mark.asyncio
async def test_interacciones_agrupadas(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client, EMAIL_ADMIN)
    resp = await api_client.get(
        "/api/auditoria/panel/interacciones",
        params={
            "desde": NOW.replace(hour=0).isoformat(),
            "hasta": NOW.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()["items"]) >= 2
