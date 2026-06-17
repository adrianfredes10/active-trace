"""Repository de tareas — C-16."""

import uuid
from collections.abc import Sequence

from sqlalchemy import or_, select

from app.models.tarea import ComentarioTarea, EstadoTarea, Tarea
from app.repositories.base import BaseRepository


class TareaRepository(BaseRepository[Tarea]):
    model = Tarea

    async def list_mias(self, usuario_id: uuid.UUID) -> Sequence[Tarea]:
        result = await self.session.execute(
            self._base_query()
            .where(Tarea.asignado_a == usuario_id)
            .order_by(Tarea.created_at.desc())
        )
        return result.scalars().all()

    async def list_admin(
        self,
        *,
        asignado_a: uuid.UUID | None = None,
        asignado_por: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
        estado: EstadoTarea | None = None,
        busqueda: str | None = None,
    ) -> Sequence[Tarea]:
        query = self._base_query()
        if asignado_a is not None:
            query = query.where(Tarea.asignado_a == asignado_a)
        if asignado_por is not None:
            query = query.where(Tarea.asignado_por == asignado_por)
        if materia_id is not None:
            query = query.where(Tarea.materia_id == materia_id)
        if estado is not None:
            query = query.where(Tarea.estado == estado)
        if busqueda:
            query = query.where(Tarea.descripcion.ilike(f"%{busqueda}%"))
        result = await self.session.execute(query.order_by(Tarea.created_at.desc()))
        return result.scalars().all()

    async def list_accesibles(self, usuario_id: uuid.UUID) -> Sequence[Tarea]:
        result = await self.session.execute(
            self._base_query()
            .where(
                or_(
                    Tarea.asignado_a == usuario_id,
                    Tarea.asignado_por == usuario_id,
                )
            )
            .order_by(Tarea.created_at.desc())
        )
        return result.scalars().all()


class ComentarioTareaRepository(BaseRepository[ComentarioTarea]):
    model = ComentarioTarea

    async def list_by_tarea(self, tarea_id: uuid.UUID) -> Sequence[ComentarioTarea]:
        result = await self.session.execute(
            self._base_query()
            .where(ComentarioTarea.tarea_id == tarea_id)
            .order_by(ComentarioTarea.creado_at.asc())
        )
        return result.scalars().all()
