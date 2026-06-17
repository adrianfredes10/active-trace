"""Repositories de encuentros — C-13."""

import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import select

from app.models.encuentro import InstanciaEncuentro, SlotEncuentro
from app.repositories.base import BaseRepository


class SlotEncuentroRepository(BaseRepository[SlotEncuentro]):
    model = SlotEncuentro


class InstanciaEncuentroRepository(BaseRepository[InstanciaEncuentro]):
    model = InstanciaEncuentro

    async def list_by_materia(
        self, materia_id: uuid.UUID, *, desde: date | None = None
    ) -> Sequence[InstanciaEncuentro]:
        query = self._base_query().where(InstanciaEncuentro.materia_id == materia_id)
        if desde is not None:
            query = query.where(InstanciaEncuentro.fecha >= desde)
        query = query.order_by(InstanciaEncuentro.fecha, InstanciaEncuentro.hora)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_slot(self, slot_id: uuid.UUID) -> Sequence[InstanciaEncuentro]:
        result = await self.session.execute(
            self._base_query().where(InstanciaEncuentro.slot_id == slot_id)
        )
        return result.scalars().all()

    async def list_tenant(self) -> Sequence[InstanciaEncuentro]:
        result = await self.session.execute(
            self._base_query().order_by(
                InstanciaEncuentro.fecha, InstanciaEncuentro.hora
            )
        )
        return result.scalars().all()
