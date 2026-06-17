"""Repository append-only del audit log (C-05) + consultas panel (C-19)."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import Date, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


@dataclass(frozen=True)
class AccionPorDiaRow:
    dia: date
    accion: str
    total: int


@dataclass(frozen=True)
class InteraccionRow:
    actor_id: uuid.UUID
    materia_id: uuid.UUID | None
    accion: str
    total: int


class AuditLogRepository:
    """Solo append y lectura tenant-scoped. Sin update/delete."""

    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def _scoped(
        self,
        query,
        *,
        materia_ids: set[uuid.UUID] | None,
        actor_scope: uuid.UUID | None,
    ):
        if materia_ids is None:
            return query
        return query.where(
            or_(
                AuditLog.materia_id.in_(materia_ids),
                AuditLog.actor_id == actor_scope,
            )
        )

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

    async def list_filtered(
        self,
        *,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        materia_id: uuid.UUID | None = None,
        actor_id: uuid.UUID | None = None,
        accion: str | None = None,
        materia_ids: set[uuid.UUID] | None = None,
        actor_scope: uuid.UUID | None = None,
        limit: int = 200,
    ) -> Sequence[AuditLog]:
        query = select(AuditLog).where(AuditLog.tenant_id == self.tenant_id)
        query = self._scoped(query, materia_ids=materia_ids, actor_scope=actor_scope)
        if desde is not None:
            query = query.where(AuditLog.fecha_hora >= desde)
        if hasta is not None:
            query = query.where(AuditLog.fecha_hora <= hasta)
        if materia_id is not None:
            query = query.where(AuditLog.materia_id == materia_id)
        if actor_id is not None:
            query = query.where(AuditLog.actor_id == actor_id)
        if accion is not None:
            query = query.where(AuditLog.accion == accion)
        result = await self.session.execute(
            query.order_by(AuditLog.fecha_hora.desc()).limit(limit)
        )
        return result.scalars().all()

    async def acciones_por_dia(
        self,
        *,
        desde: datetime,
        hasta: datetime,
        materia_ids: set[uuid.UUID] | None = None,
        actor_scope: uuid.UUID | None = None,
    ) -> list[AccionPorDiaRow]:
        dia_col = cast(AuditLog.fecha_hora, Date).label("dia")
        query = (
            select(dia_col, AuditLog.accion, func.count().label("total"))
            .where(
                AuditLog.tenant_id == self.tenant_id,
                AuditLog.fecha_hora >= desde,
                AuditLog.fecha_hora <= hasta,
            )
            .group_by(dia_col, AuditLog.accion)
            .order_by(dia_col)
        )
        query = self._scoped(query, materia_ids=materia_ids, actor_scope=actor_scope)
        result = await self.session.execute(query)
        return [
            AccionPorDiaRow(dia=row.dia, accion=row.accion, total=int(row.total))
            for row in result.all()
        ]

    async def interacciones_agrupadas(
        self,
        *,
        desde: datetime,
        hasta: datetime,
        materia_ids: set[uuid.UUID] | None = None,
        actor_scope: uuid.UUID | None = None,
    ) -> list[InteraccionRow]:
        query = (
            select(
                AuditLog.actor_id,
                AuditLog.materia_id,
                AuditLog.accion,
                func.count().label("total"),
            )
            .where(
                AuditLog.tenant_id == self.tenant_id,
                AuditLog.fecha_hora >= desde,
                AuditLog.fecha_hora <= hasta,
            )
            .group_by(AuditLog.actor_id, AuditLog.materia_id, AuditLog.accion)
        )
        query = self._scoped(query, materia_ids=materia_ids, actor_scope=actor_scope)
        result = await self.session.execute(query)
        return [
            InteraccionRow(
                actor_id=row.actor_id,
                materia_id=row.materia_id,
                accion=row.accion,
                total=int(row.total),
            )
            for row in result.all()
        ]

    async def get(self, entry_id: uuid.UUID) -> AuditLog | None:
        result = await self.session.execute(
            select(AuditLog).where(
                AuditLog.tenant_id == self.tenant_id,
                AuditLog.id == entry_id,
            )
        )
        return result.scalar_one_or_none()
