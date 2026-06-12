"""Repositories de estructura académica (C-06)."""

import uuid

from sqlalchemy import select

from app.models.estructura import Carrera, Cohorte, Materia
from app.repositories.base import BaseRepository


class CarreraRepository(BaseRepository[Carrera]):
    model = Carrera

    async def get_by_codigo(self, codigo: str) -> Carrera | None:
        result = await self.session.execute(
            self._base_query().where(self.model.codigo == codigo)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Carrera]:
        result = await self.session.execute(
            self._base_query().order_by(self.model.codigo)
        )
        return list(result.scalars().all())


class CohorteRepository(BaseRepository[Cohorte]):
    model = Cohorte

    async def get_by_nombre(
        self,
        *,
        carrera_id: uuid.UUID,
        nombre: str,
    ) -> Cohorte | None:
        result = await self.session.execute(
            self._base_query().where(
                self.model.carrera_id == carrera_id,
                self.model.nombre == nombre,
            )
        )
        return result.scalar_one_or_none()

    async def list_all(self, *, carrera_id: uuid.UUID | None = None) -> list[Cohorte]:
        query = self._base_query()
        if carrera_id is not None:
            query = query.where(self.model.carrera_id == carrera_id)
        result = await self.session.execute(query.order_by(self.model.nombre))
        return list(result.scalars().all())


class MateriaRepository(BaseRepository[Materia]):
    model = Materia

    async def get_by_codigo(self, codigo: str) -> Materia | None:
        result = await self.session.execute(
            self._base_query().where(self.model.codigo == codigo)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Materia]:
        result = await self.session.execute(
            self._base_query().order_by(self.model.codigo)
        )
        return list(result.scalars().all())
