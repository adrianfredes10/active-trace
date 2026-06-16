"""Repositories de calificaciones y umbrales — C-10."""

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import distinct, func, select

from app.models.calificacion import Calificacion, UmbralMateria
from app.repositories.base import BaseRepository


class CalificacionRepository(BaseRepository[Calificacion]):
    model = Calificacion

    async def list_by_asignacion(
        self, asignacion_id: uuid.UUID
    ) -> Sequence[Calificacion]:
        result = await self.session.execute(
            self._base_query().where(Calificacion.asignacion_id == asignacion_id)
        )
        return result.scalars().all()

    async def list_actividades_distintas(self, asignacion_id: uuid.UUID) -> list[str]:
        result = await self.session.execute(
            select(distinct(Calificacion.actividad))
            .where(Calificacion.tenant_id == self.tenant_id)
            .where(Calificacion.deleted_at.is_(None))
            .where(Calificacion.asignacion_id == asignacion_id)
            .order_by(Calificacion.actividad)
        )
        return list(result.scalars().all())

    async def list_by_materia_cohorte(
        self,
        materia_id: uuid.UUID,
        *,
        asignacion_id: uuid.UUID | None = None,
        importado_desde: datetime | None = None,
        importado_hasta: datetime | None = None,
    ) -> Sequence[Calificacion]:
        query = self._base_query().where(Calificacion.materia_id == materia_id)
        if asignacion_id is not None:
            query = query.where(Calificacion.asignacion_id == asignacion_id)
        if importado_desde is not None:
            query = query.where(Calificacion.importado_at >= importado_desde)
        if importado_hasta is not None:
            query = query.where(Calificacion.importado_at <= importado_hasta)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def count_by_asignacion(self, asignacion_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Calificacion)
            .where(Calificacion.tenant_id == self.tenant_id)
            .where(Calificacion.deleted_at.is_(None))
            .where(Calificacion.asignacion_id == asignacion_id)
        )
        return int(result.scalar_one())

    async def get_by_clave(
        self,
        asignacion_id: uuid.UUID,
        entrada_padron_id: uuid.UUID,
        actividad: str,
    ) -> Calificacion | None:
        result = await self.session.execute(
            self._base_query()
            .where(Calificacion.asignacion_id == asignacion_id)
            .where(Calificacion.entrada_padron_id == entrada_padron_id)
            .where(Calificacion.actividad == actividad)
        )
        return result.scalar_one_or_none()


class UmbralMateriaRepository(BaseRepository[UmbralMateria]):
    model = UmbralMateria

    async def get_by_asignacion(
        self, asignacion_id: uuid.UUID
    ) -> UmbralMateria | None:
        result = await self.session.execute(
            self._base_query().where(UmbralMateria.asignacion_id == asignacion_id)
        )
        return result.scalar_one_or_none()
