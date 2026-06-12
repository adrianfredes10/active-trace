"""Repository append-only del audit log (C-05)."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


class AuditLogRepository:
    """Solo append y lectura tenant-scoped. Sin update/delete."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    async def append(self, entry: AuditLog) -> AuditLog:
        entry.tenant_id = self.tenant_id
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_recent(self, *, limit: int = 50) -> Sequence[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == self.tenant_id)
            .order_by(AuditLog.fecha_hora.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get(self, entry_id: uuid.UUID) -> AuditLog | None:
        result = await self.session.execute(
            select(AuditLog).where(
                AuditLog.tenant_id == self.tenant_id,
                AuditLog.id == entry_id,
            )
        )
        return result.scalar_one_or_none()
