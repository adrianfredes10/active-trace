"""Repository de guardias — C-13."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models.encuentro import Guardia
from app.repositories.base import BaseRepository


class GuardiaRepository(BaseRepository[Guardia]):
    model = Guardia

    async def list_filtered(
        self,
        *,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
    ) -> Sequence[Guardia]:
        query = self._base_query().order_by(Guardia.creada_at.desc())
        if materia_id is not None:
            query = query.where(Guardia.materia_id == materia_id)
        if cohorte_id is not None:
            query = query.where(Guardia.cohorte_id == cohorte_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_asignacion(
        self, asignacion_id: uuid.UUID
    ) -> Sequence[Guardia]:
        result = await self.session.execute(
            self._base_query()
            .where(Guardia.asignacion_id == asignacion_id)
            .order_by(Guardia.creada_at.desc())
        )
        return result.scalars().all()
