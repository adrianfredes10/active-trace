import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.security import email_blind_index, hash_password
from app.models import AuditLog, Tenant, Usuario
from app.services.audit_service import AuditContext, AuditService, InvalidAuditAction

TENANT = uuid.UUID("00000000-0000-0000-0000-000000000501")
ACTOR = uuid.UUID("00000000-0000-0000-0000-000000000502")


async def _seed(session: AsyncSession) -> None:
    session.add(Tenant(id=TENANT, nombre="Audit", slug="audit-test"))
    session.add(
        Usuario(
            id=ACTOR,
            tenant_id=TENANT,
            email="actor@audit.test",
            email_hash=email_blind_index("actor@audit.test"),
            password_hash=hash_password("pw"),
        )
    )
    await session.flush()


@pytest.mark.asyncio
async def test_record_persists_entry(session: AsyncSession, settings) -> None:
    await _seed(session)
    ctx = AuditContext(actor_id=ACTOR, tenant_id=TENANT, ip="127.0.0.1")
    entry = await AuditService(session, TENANT).record(
        ctx,
        accion=AuditAction.PADRON_CARGAR,
        detalle={"version": 1},
        filas_afectadas=42,
    )
    await session.commit()
    assert entry.accion == "PADRON_CARGAR"
    assert entry.filas_afectadas == 42
    assert entry.actor_id == ACTOR


@pytest.mark.asyncio
async def test_record_rejects_unknown_action(session: AsyncSession, settings) -> None:
    await _seed(session)
    ctx = AuditContext(actor_id=ACTOR, tenant_id=TENANT)
    with pytest.raises(InvalidAuditAction):
        await AuditService(session, TENANT).record(ctx, accion="CODIGO_INVENTADO")


@pytest.mark.asyncio
async def test_impersonation_attributes_actor_not_impersonado(
    session: AsyncSession, settings
) -> None:
    await _seed(session)
    target = uuid.uuid4()
    session.add(
        Usuario(
            id=target,
            tenant_id=TENANT,
            email="target@audit.test",
            email_hash=email_blind_index("target@audit.test"),
            password_hash=hash_password("pw"),
        )
    )
    await session.flush()
    ctx = AuditContext(
        actor_id=ACTOR, tenant_id=TENANT, impersonado_id=target
    )
    entry = await AuditService(session, TENANT).record(
        ctx, accion=AuditAction.IMPERSONACION_INICIAR
    )
    assert entry.actor_id == ACTOR
    assert entry.impersonado_id == target


@pytest.mark.asyncio
async def test_append_only_rejects_update(session: AsyncSession, settings) -> None:
    await _seed(session)
    ctx = AuditContext(actor_id=ACTOR, tenant_id=TENANT)
    entry = await AuditService(session, TENANT).record(
        ctx, accion=AuditAction.COMUNICACION_ENVIAR
    )
    await session.commit()
    with pytest.raises(DBAPIError):
        await session.execute(
            text("UPDATE audit_logs SET accion = 'X' WHERE id = :id"),
            {"id": entry.id},
        )
        await session.commit()
