"""Tests API comunicaciones — C-12."""

import uuid
from datetime import date

import pytest
from sqlalchemy import select

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.rbac_seed import seed_tenant_rbac
from app.workers.comunicacion_worker import procesar_pendientes

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c12")
SLUG = "c12-api"
EMAIL_PROF = "prof@c12.example.com"
EMAIL_COORD = "coord@c12.example.com"
PW = "S3cret!pass"

PADRON_CSV = b"""nombre,apellidos,email,comision
Ana,Garcia,ana@example.com,A
Pedro,Lopez,pedro@example.com,B
"""

PAYLOAD_BASE = {
    "asunto": "Recordatorio {{nombre}}",
    "cuerpo": "Estimado/a {{nombre}} {{apellidos}}, revise sus entregas.",
    "confirmo_preview": True,
}


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(
            Tenant(
                id=TENANT_ID,
                nombre="C12",
                slug=SLUG,
                aprobacion_masiva_comunicaciones=True,
            )
        )
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
        await session.commit()

    return {
        "materia_id": str(materia.id),
        "cohorte_id": str(cohorte.id),
        "carrera_id": str(carrera.id),
        "prof_id": str(users[EMAIL_PROF].id),
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
async def test_enviar_rechaza_destinatario_fuera_de_comision(api_client) -> None:
    """1.5 — 403 si destinatario no pertenece a comisión permitida."""
    import io

    ctx = await _seed(api_client)
    factory = get_session_factory()
    async with factory() as session:
        asig = Asignacion(
            tenant_id=TENANT_ID,
            usuario_id=uuid.UUID(ctx["prof_id"]),
            rol=RolAsignacion.profesor,
            materia_id=uuid.UUID(ctx["materia_id"]),
            carrera_id=uuid.UUID(ctx["carrera_id"]),
            cohorte_id=uuid.UUID(ctx["cohorte_id"]),
            comisiones=["A"],
            desde=date(2026, 3, 1),
        )
        session.add(asig)
        await session.commit()

    headers = await _headers(api_client, EMAIL_PROF)
    coord_headers = await _headers(api_client, EMAIL_COORD)
    padron = await api_client.post(
        "/api/padron/importar",
        data={"materia_id": ctx["materia_id"], "cohorte_id": ctx["cohorte_id"]},
        files={"file": ("padron.csv", io.BytesIO(PADRON_CSV), "text/csv")},
        headers=coord_headers,
    )
    assert padron.status_code == 201

    resp = await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "materia_id": ctx["materia_id"],
            "destinatarios": [
                {
                    "email": "pedro@example.com",
                    "nombre": "Pedro",
                    "apellidos": "Lopez",
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_preview_renderiza_variables(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.post(
        "/api/comunicaciones/preview",
        json={
            "asunto": PAYLOAD_BASE["asunto"],
            "cuerpo": PAYLOAD_BASE["cuerpo"],
            "muestra": {
                "email": "ana@example.com",
                "nombre": "Ana",
                "apellidos": "Garcia",
            },
        },
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["asunto"] == "Recordatorio Ana"


@pytest.mark.asyncio
async def test_enviar_sin_preview_falla(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "confirmo_preview": False,
            "materia_id": ctx["materia_id"],
            "destinatarios": [
                {
                    "email": "ana@example.com",
                    "nombre": "Ana",
                    "apellidos": "Garcia",
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_masivo_requiere_aprobacion_y_worker_espera(api_client, session) -> None:
    ctx = await _seed(api_client)
    headers_prof = await _headers(api_client, EMAIL_PROF)
    destinatarios = [
        {"email": "ana@example.com", "nombre": "Ana", "apellidos": "Garcia"},
        {"email": "pedro@example.com", "nombre": "Pedro", "apellidos": "Lopez"},
    ]
    resp = await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "materia_id": ctx["materia_id"],
            "destinatarios": destinatarios,
        },
        headers=headers_prof,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["requiere_aprobacion"] is True
    assert body["encoladas"] == 2
    lote_id = body["lote_id"]

    procesadas = await procesar_pendientes(session, TENANT_ID)
    assert procesadas == 0

    headers_coord = await _headers(api_client, EMAIL_COORD)
    apr = await api_client.post(
        f"/api/comunicaciones/lotes/{lote_id}/aprobar",
        headers=headers_coord,
    )
    assert apr.status_code == 200
    assert apr.json()["aprobadas"] == 2

    procesadas = await procesar_pendientes(session, TENANT_ID)
    assert procesadas == 2
    await session.commit()

    lote = await api_client.get(
        f"/api/comunicaciones/lotes/{lote_id}", headers=headers_prof
    )
    estados = {i["estado"] for i in lote.json()["items"]}
    assert estados == {"Enviado"}


@pytest.mark.asyncio
async def test_individual_envia_sin_aprobacion(api_client, session) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "materia_id": ctx["materia_id"],
            "destinatarios": [
                {
                    "email": "ana@example.com",
                    "nombre": "Ana",
                    "apellidos": "Garcia",
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["requiere_aprobacion"] is False

    procesadas = await procesar_pendientes(session, TENANT_ID)
    assert procesadas == 1
    await session.commit()
    item = resp.json()["items"][0]
    lote = await api_client.get(
        f"/api/comunicaciones/lotes/{resp.json()['lote_id']}",
        headers=headers,
    )
    assert lote.json()["items"][0]["estado"] == "Enviado"
    assert lote.json()["items"][0]["id"] == item["id"]


@pytest.mark.asyncio
async def test_cancelar_pendiente(api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "materia_id": ctx["materia_id"],
            "destinatarios": [
                {
                    "email": "ana@example.com",
                    "nombre": "Ana",
                    "apellidos": "Garcia",
                },
                {
                    "email": "pedro@example.com",
                    "nombre": "Pedro",
                    "apellidos": "Lopez",
                },
            ],
        },
        headers=headers,
    )
    item_id = resp.json()["items"][0]["id"]
    cancel = await api_client.post(
        f"/api/comunicaciones/{item_id}/cancelar",
        headers=headers,
    )
    assert cancel.status_code == 200
    assert cancel.json()["estado"] == "Cancelado"


@pytest.mark.asyncio
async def test_destinatario_cifrado_en_bd(session, api_client) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "materia_id": ctx["materia_id"],
            "destinatarios": [
                {
                    "email": "ana@example.com",
                    "nombre": "Ana",
                    "apellidos": "Garcia",
                }
            ],
        },
        headers=headers,
    )
    result = await session.execute(
        select(Comunicacion).where(Comunicacion.tenant_id == TENANT_ID)
    )
    row = result.scalars().first()
    assert row is not None
    assert row.destinatario == "ana@example.com"

    from sqlalchemy import text

    db_val = (
        await session.execute(
            text("SELECT destinatario FROM comunicaciones WHERE id = :id"),
            {"id": row.id},
        )
    ).scalar_one()
    assert db_val != "ana@example.com"
    assert len(db_val) > len("ana@example.com")


@pytest.mark.asyncio
async def test_worker_marca_error(api_client, session) -> None:
    ctx = await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.post(
        "/api/comunicaciones/enviar",
        json={
            **PAYLOAD_BASE,
            "materia_id": ctx["materia_id"],
            "destinatarios": [
                {
                    "email": "falla@fail.example.com",
                    "nombre": "Falla",
                    "apellidos": "Mail",
                }
            ],
        },
        headers=headers,
    )
    await session.commit()
    await procesar_pendientes(session, TENANT_ID)
    await session.commit()
    lote = await api_client.get(
        f"/api/comunicaciones/lotes/{resp.json()['lote_id']}",
        headers=headers,
    )
    assert lote.json()["items"][0]["estado"] == "Error"
