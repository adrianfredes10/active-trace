"""Tests API liquidaciones y facturas (C-18)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.database import get_session_factory
from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.audit_log import AuditLog
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.models.liquidacion import Liquidacion, LiquidacionEstado, SalarioBase
from app.repositories.rbac_repository import RolRepository, UsuarioRolRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.services.liquidacion_service import LiquidacionService
from app.services.rbac_seed import seed_tenant_rbac

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c18")
SLUG = "c18-api"
EMAIL_FIN = "finanzas@c18.example.com"
EMAIL_PROF = "prof@c18.example.com"
EMAIL_FACT = "fact@c18.example.com"
PW = "S3cret!pass"
PERIODO = "2026-06"


async def _seed(api_client) -> dict:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="C18", slug=SLUG))
        await session.flush()
        await seed_tenant_rbac(session, TENANT_ID)

        users: dict[str, Usuario] = {}
        for email, role, nombre, facturador in [
            (EMAIL_FIN, "FINANZAS", "Fin", False),
            (EMAIL_PROF, "PROFESOR", "Prof", False),
            (EMAIL_FACT, "PROFESOR", "Fact", True),
        ]:
            u = await UsuarioRepository(session, TENANT_ID).add(
                Usuario(
                    email=email,
                    email_hash=email_blind_index(email),
                    password_hash=hash_password(PW),
                    nombre=nombre,
                    apellidos="C18",
                    facturador=facturador,
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
        materia_prog = Materia(
            tenant_id=TENANT_ID,
            codigo="PRG1",
            nombre="Programación 1",
            plus_grupo="PROG",
            estado=EntidadEstado.ACTIVA,
        )
        session.add_all([cohorte, materia_prog])
        await session.flush()

        session.add(
            SalarioBase(
                tenant_id=TENANT_ID,
                rol=RolAsignacion.profesor,
                monto=Decimal("100000"),
                vig_desde=date(2026, 1, 1),
            )
        )
        from app.models.liquidacion import SalarioPlus

        session.add(
            SalarioPlus(
                tenant_id=TENANT_ID,
                grupo="PROG",
                rol=RolAsignacion.profesor,
                monto=Decimal("5000"),
                vig_desde=date(2026, 1, 1),
                descripcion="Plus programación",
            )
        )

        prof = users[EMAIL_PROF]
        session.add(
            Asignacion(
                tenant_id=TENANT_ID,
                usuario_id=prof.id,
                rol=RolAsignacion.profesor,
                materia_id=materia_prog.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                comisiones=["A", "B", "C"],
                desde=date(2026, 3, 1),
            )
        )
        fact = users[EMAIL_FACT]
        session.add(
            Asignacion(
                tenant_id=TENANT_ID,
                usuario_id=fact.id,
                rol=RolAsignacion.profesor,
                materia_id=materia_prog.id,
                carrera_id=carrera.id,
                cohorte_id=cohorte.id,
                comisiones=["A"],
                desde=date(2026, 3, 1),
            )
        )
        await session.commit()

    return {
        "cohorte_id": str(cohorte.id),
        "prof_id": str(users[EMAIL_PROF].id),
        "fact_id": str(users[EMAIL_FACT].id),
    }


async def _login(api_client, email: str) -> str:
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": email, "password": PW},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


async def _headers(api_client, email: str = EMAIL_FIN) -> dict:
    return {"Authorization": f"Bearer {await _login(api_client, email)}"}


async def test_calculo_base_plus_acumula_comisiones(api_client, session) -> None:
    """RN-33/34: 3 comisiones PROG → base 100k + 3×5k plus = 115k."""
    await _seed(api_client)
    svc = LiquidacionService(session, TENANT_ID)
    await svc.calcular_periodo(PERIODO)
    await session.commit()

    liqs = await svc.listar(PERIODO, "general")
    assert len(liqs) == 1
    assert liqs[0].monto_base == Decimal("100000")
    assert liqs[0].monto_plus == Decimal("15000")
    assert liqs[0].total == Decimal("115000")


async def test_facturador_excluido_segmento_factura(api_client, session) -> None:
    await _seed(api_client)
    svc = LiquidacionService(session, TENANT_ID)
    await svc.calcular_periodo(PERIODO)
    await session.commit()

    factura_seg = await svc.listar(PERIODO, "factura")
    assert len(factura_seg) == 1
    assert factura_seg[0].excluido_por_factura is True
    assert factura_seg[0].total == Decimal("0")

    general = await svc.listar(PERIODO, "general")
    assert all(not l.excluido_por_factura for l in general)


async def test_cierre_inmutable_y_auditoria(api_client, session) -> None:
    await _seed(api_client)
    headers = await _headers(api_client)

    list_resp = await api_client.get(
        f"/api/liquidaciones?periodo={PERIODO}&segmento=general",
        headers=headers,
    )
    assert list_resp.status_code == 200
    liq_id = list_resp.json()["items"][0]["id"]

    cerrar = await api_client.post(
        f"/api/liquidaciones/{liq_id}/cerrar",
        headers=headers,
    )
    assert cerrar.status_code == 200
    assert cerrar.json()["estado"] == "Cerrada"

    again = await api_client.post(
        f"/api/liquidaciones/{liq_id}/cerrar",
        headers=headers,
    )
    assert again.status_code == 409

    audit = await session.execute(
        select(AuditLog).where(AuditLog.accion == "LIQUIDACION_CERRAR")
    )
    assert audit.scalar_one_or_none() is not None


async def test_api_kpis_y_grilla(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client)

    kpis = await api_client.get(
        f"/api/liquidaciones/kpis?periodo={PERIODO}",
        headers=headers,
    )
    assert kpis.status_code == 200
    body = kpis.json()
    assert body["total_general"] == "115000.00"
    assert body["cantidad_abiertas"] >= 1

    grilla = await api_client.get("/api/liquidaciones/grilla", headers=headers)
    assert grilla.status_code == 200
    assert len(grilla.json()["items"]) >= 1

    nueva = await api_client.post(
        "/api/liquidaciones/grilla/base",
        headers=headers,
        json={
            "rol": "TUTOR",
            "monto": "80000",
            "vig_desde": "2026-06-01",
        },
    )
    assert nueva.status_code == 201
    assert nueva.json()["rol"] == "TUTOR"


async def test_factura_flujo(api_client) -> None:
    data = await _seed(api_client)
    headers = await _headers(api_client)

    crear = await api_client.post(
        "/api/facturas",
        headers=headers,
        json={
            "usuario_id": data["fact_id"],
            "periodo": PERIODO,
            "detalle": "Honorarios junio",
            "referencia_archivo": "s3://fact.pdf",
            "tamano_kb": "120.5",
        },
    )
    assert crear.status_code == 201
    factura_id = crear.json()["id"]

    abonar = await api_client.post(
        f"/api/facturas/{factura_id}/abonar",
        headers=headers,
    )
    assert abonar.status_code == 200
    assert abonar.json()["estado"] == "Abonada"


async def test_profesor_sin_permiso_403(api_client) -> None:
    await _seed(api_client)
    headers = await _headers(api_client, EMAIL_PROF)
    resp = await api_client.get(
        f"/api/liquidaciones?periodo={PERIODO}&segmento=general",
        headers=headers,
    )
    assert resp.status_code == 403
