"""Repository de asignaciones (tenant-scoped).

Solo expone asignaciones vigentes en `list_vigentes_*`; el histórico
completo está disponible via `list` heredado del base.
"""

import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import select

from app.models.asignacion import Asignacion
from app.repositories.base import BaseRepository


class AsignacionRepository(BaseRepository[Asignacion]):
    model = Asignacion

    async def list_vigentes_by_usuario(
        self, usuario_id: uuid.UUID
    ) -> Sequence[Asignacion]:
        hoy = date.today()
        result = await self.session.execute(
            self._base_query()
            .where(Asignacion.usuario_id == usuario_id)
            .where(Asignacion.desde <= hoy)
            .where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= hoy)
            )
        )
        return result.scalars().all()

    async def list_vigentes_by_materia(
        self, materia_id: uuid.UUID
    ) -> Sequence[Asignacion]:
        hoy = date.today()
        result = await self.session.execute(
            self._base_query()
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.desde <= hoy)
            .where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= hoy)
            )
        )
        return result.scalars().all()

    async def list_by_equipo(
        self,
        *,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
    ) -> Sequence[Asignacion]:
        result = await self.session.execute(
            self._base_query()
            .where(Asignacion.materia_id == materia_id)
            .where(Asignacion.carrera_id == carrera_id)
            .where(Asignacion.cohorte_id == cohorte_id)
        )
        return result.scalars().all()

    async def list_by_usuario(
        self,
        usuario_id: uuid.UUID,
        *,
        solo_vigentes: bool = False,
    ) -> Sequence[Asignacion]:
        query = self._base_query().where(Asignacion.usuario_id == usuario_id)
        if solo_vigentes:
            hoy = date.today()
            query = query.where(Asignacion.desde <= hoy).where(
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= hoy)
            )
        result = await self.session.execute(query)
        return result.scalars().all()
