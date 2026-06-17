"""Repository de comunicaciones — C-12."""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, select

from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class ComunicacionEstadoRow:
    enviado_por: uuid.UUID
    estado: str
    total: int


class ComunicacionRepository(BaseRepository[Comunicacion]):
    model = Comunicacion

    async def list_by_lote(self, lote_id: uuid.UUID) -> Sequence[Comunicacion]:
        result = await self.session.execute(
            self._base_query().where(Comunicacion.lote_id == lote_id)
        )
        return result.scalars().all()

    async def list_pendientes_despacho(
        self, *, limit: int = 50
    ) -> Sequence[Comunicacion]:
        result = await self.session.execute(
            self._base_query()
            .where(Comunicacion.estado == EstadoComunicacion.pendiente)
            .order_by(Comunicacion.created_at)
            .limit(limit)
        )
        return result.scalars().all()

    async def add_many(self, items: list[Comunicacion]) -> list[Comunicacion]:
        for item in items:
            item.tenant_id = self.tenant_id
            self.session.add(item)
        await self.session.flush()
        return items

    async def estados_por_docente(
        self, *, materia_ids: set[uuid.UUID] | None = None
    ) -> list[ComunicacionEstadoRow]:
        query = (
            select(
                Comunicacion.enviado_por,
                Comunicacion.estado,
                func.count().label("total"),
            )
            .where(
                Comunicacion.tenant_id == self.tenant_id,
                Comunicacion.deleted_at.is_(None),
            )
            .group_by(Comunicacion.enviado_por, Comunicacion.estado)
        )
        if materia_ids is not None:
            query = query.where(Comunicacion.materia_id.in_(materia_ids))
        result = await self.session.execute(query)
        return [
            ComunicacionEstadoRow(
                enviado_por=row.enviado_por,
                estado=row.estado.value if hasattr(row.estado, "value") else str(row.estado),
                total=int(row.total),
            )
            for row in result.all()
        ]
