"""Tests C-07: campos PII en Usuario y modelo Asignacion.

RED — corren en rojo hasta que se implemente C-07.
"""

import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import email_blind_index, hash_password
from app.models import Tenant, Usuario
from app.models.asignacion import Asignacion, RolAsignacion

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000c07")


async def _seed_tenant(session: AsyncSession) -> None:
    session.add(Tenant(id=TENANT_ID, nombre="C07", slug="c07"))
    await session.flush()


def _usuario(*, nombre: str = "Ana", apellidos: str = "García") -> Usuario:
    return Usuario(
        tenant_id=TENANT_ID,
        email="ana@test.com",
        email_hash=email_blind_index("ana@test.com"),
        password_hash=hash_password("pass"),
        nombre=nombre,
        apellidos=apellidos,
        dni="12345678",
        cuil="20123456789",
    )


# ---------------------------------------------------------------------------
# PII cifrada — round-trip
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_usuario_pii_persists_and_decrypts(
    session: AsyncSession, settings
) -> None:
    """DNI y CUIL se cifran en reposo y se descifran al leer."""
    await _seed_tenant(session)
    u = _usuario()
    session.add(u)
    await session.flush()
    await session.refresh(u)

    assert u.dni == "12345678"
    assert u.cuil == "20123456789"


@pytest.mark.asyncio
async def test_usuario_repr_no_leak_pii(settings) -> None:
    """repr() no expone DNI, CUIL, CBU ni email."""
    u = _usuario()
    r = repr(u)
    assert "12345678" not in r
    assert "20123456789" not in r
    assert "ana@test.com" not in r


@pytest.mark.asyncio
async def test_usuario_nombre_apellidos_not_required_in_auth_fields(
    session: AsyncSession, settings
) -> None:
    """nombre/apellidos pueden guardarse y consultarse correctamente."""
    await _seed_tenant(session)
    u = _usuario(nombre="Pedro", apellidos="López")
    session.add(u)
    await session.flush()
    await session.refresh(u)

    assert u.nombre == "Pedro"
    assert u.apellidos == "López"


# ---------------------------------------------------------------------------
# Asignacion — vigencia
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_asignacion_vigente_true_when_no_hasta(
    session: AsyncSession, settings
) -> None:
    """Una asignacion sin fecha hasta está vigente."""
    await _seed_tenant(session)
    u = _usuario()
    session.add(u)
    await session.flush()

    asig = Asignacion(
        tenant_id=TENANT_ID,
        usuario_id=u.id,
        rol=RolAsignacion.profesor,
        desde=date.today() - timedelta(days=10),
        hasta=None,
    )
    session.add(asig)
    await session.flush()
    await session.refresh(asig)

    assert asig.vigente is True


@pytest.mark.asyncio
async def test_asignacion_vencida_when_hasta_pasado(
    session: AsyncSession, settings
) -> None:
    """Una asignacion con hasta < hoy está vencida."""
    await _seed_tenant(session)
    u = _usuario()
    session.add(u)
    await session.flush()

    asig = Asignacion(
        tenant_id=TENANT_ID,
        usuario_id=u.id,
        rol=RolAsignacion.tutor,
        desde=date.today() - timedelta(days=60),
        hasta=date.today() - timedelta(days=1),
    )
    session.add(asig)
    await session.flush()

    assert asig.vigente is False


@pytest.mark.asyncio
async def test_asignacion_multi_rol_mismo_usuario(
    session: AsyncSession, settings
) -> None:
    """Un usuario puede tener múltiples asignaciones con distintos roles."""
    await _seed_tenant(session)
    u = _usuario()
    session.add(u)
    await session.flush()

    a1 = Asignacion(
        tenant_id=TENANT_ID,
        usuario_id=u.id,
        rol=RolAsignacion.profesor,
        desde=date.today(),
    )
    a2 = Asignacion(
        tenant_id=TENANT_ID,
        usuario_id=u.id,
        rol=RolAsignacion.coordinador,
        desde=date.today(),
    )
    session.add_all([a1, a2])
    await session.flush()

    assert a1.id != a2.id
    assert a1.vigente is True
    assert a2.vigente is True


@pytest.mark.asyncio
async def test_asignacion_tenant_isolation(
    session: AsyncSession, settings
) -> None:
    """Asignaciones pertenecen al tenant del usuario."""
    await _seed_tenant(session)
    u = _usuario()
    session.add(u)
    await session.flush()

    asig = Asignacion(
        tenant_id=TENANT_ID,
        usuario_id=u.id,
        rol=RolAsignacion.admin,
        desde=date.today(),
    )
    session.add(asig)
    await session.flush()
    await session.refresh(asig)

    assert asig.tenant_id == TENANT_ID
