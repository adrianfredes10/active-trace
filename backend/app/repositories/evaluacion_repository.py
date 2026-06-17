"""Repository de evaluaciones — C-14."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.evaluacion import (
    ConvocadoEvaluacion,
    EstadoEvaluacion,
    EstadoReservaEvaluacion,
    Evaluacion,
    ReservaEvaluacion,
    ResultadoEvaluacion,
    TurnoEvaluacion,
)
from app.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    model = Evaluacion

    async def list_abiertas(self) -> Sequence[Evaluacion]:
        result = await self.session.execute(
            self._base_query()
            .where(Evaluacion.estado == EstadoEvaluacion.abierta)
            .order_by(Evaluacion.created_at.desc())
        )
        return result.scalars().all()


class TurnoEvaluacionRepository(BaseRepository[TurnoEvaluacion]):
    model = TurnoEvaluacion

    async def list_by_evaluacion(
        self, evaluacion_id: uuid.UUID
    ) -> Sequence[TurnoEvaluacion]:
        result = await self.session.execute(
            self._base_query()
            .where(TurnoEvaluacion.evaluacion_id == evaluacion_id)
            .order_by(TurnoEvaluacion.fecha, TurnoEvaluacion.hora)
        )
        return result.scalars().all()


class ConvocadoEvaluacionRepository(BaseRepository[ConvocadoEvaluacion]):
    model = ConvocadoEvaluacion

    async def count_by_evaluacion(self, evaluacion_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ConvocadoEvaluacion)
            .where(
                ConvocadoEvaluacion.tenant_id == self.tenant_id,
                ConvocadoEvaluacion.evaluacion_id == evaluacion_id,
                ConvocadoEvaluacion.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def is_convocado(self, evaluacion_id: uuid.UUID, alumno_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            self._base_query().where(
                ConvocadoEvaluacion.evaluacion_id == evaluacion_id,
                ConvocadoEvaluacion.alumno_id == alumno_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_by_evaluacion(
        self, evaluacion_id: uuid.UUID
    ) -> Sequence[ConvocadoEvaluacion]:
        result = await self.session.execute(
            self._base_query().where(ConvocadoEvaluacion.evaluacion_id == evaluacion_id)
        )
        return result.scalars().all()


class ReservaEvaluacionRepository(BaseRepository[ReservaEvaluacion]):
    model = ReservaEvaluacion

    async def count_activas_por_turno(self, turno_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ReservaEvaluacion)
            .where(
                ReservaEvaluacion.tenant_id == self.tenant_id,
                ReservaEvaluacion.turno_id == turno_id,
                ReservaEvaluacion.estado == EstadoReservaEvaluacion.activa,
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def tiene_reserva_activa(
        self, evaluacion_id: uuid.UUID, alumno_id: uuid.UUID
    ) -> bool:
        result = await self.session.execute(
            self._base_query().where(
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.alumno_id == alumno_id,
                ReservaEvaluacion.estado == EstadoReservaEvaluacion.activa,
            )
        )
        return result.scalar_one_or_none() is not None

    async def count_activas_por_evaluacion(self, evaluacion_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ReservaEvaluacion)
            .where(
                ReservaEvaluacion.tenant_id == self.tenant_id,
                ReservaEvaluacion.evaluacion_id == evaluacion_id,
                ReservaEvaluacion.estado == EstadoReservaEvaluacion.activa,
                ReservaEvaluacion.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def list_activas(self) -> Sequence[ReservaEvaluacion]:
        result = await self.session.execute(
            self._base_query()
            .where(ReservaEvaluacion.estado == EstadoReservaEvaluacion.activa)
            .order_by(ReservaEvaluacion.fecha_hora)
        )
        return result.scalars().all()

    async def list_by_evaluacion(
        self, evaluacion_id: uuid.UUID
    ) -> Sequence[ReservaEvaluacion]:
        result = await self.session.execute(
            self._base_query()
            .where(ReservaEvaluacion.evaluacion_id == evaluacion_id)
            .order_by(ReservaEvaluacion.fecha_hora)
        )
        return result.scalars().all()


class ResultadoEvaluacionRepository(BaseRepository[ResultadoEvaluacion]):
    model = ResultadoEvaluacion

    async def count_by_evaluacion(self, evaluacion_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ResultadoEvaluacion)
            .where(
                ResultadoEvaluacion.tenant_id == self.tenant_id,
                ResultadoEvaluacion.evaluacion_id == evaluacion_id,
                ResultadoEvaluacion.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def list_all(self) -> Sequence[ResultadoEvaluacion]:
        result = await self.session.execute(
            self._base_query().order_by(ResultadoEvaluacion.created_at.desc())
        )
        return result.scalars().all()
