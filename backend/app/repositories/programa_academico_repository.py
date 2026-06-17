"""Repository de programas y fechas académicas — C-17."""

import uuid
from collections.abc import Sequence
from datetime import date

from sqlalchemy import select

from app.models.evaluacion import TipoEvaluacion
from app.models.programa_academico import FechaAcademica, ProgramaMateria
from app.repositories.base import BaseRepository


class ProgramaMateriaRepository(BaseRepository[ProgramaMateria]):
    model = ProgramaMateria

    async def list_filtered(
        self,
        *,
        materia_id: uuid.UUID | None = None,
        carrera_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
    ) -> Sequence[ProgramaMateria]:
        query = self._base_query().order_by(ProgramaMateria.cargado_at.desc())
        if materia_id is not None:
            query = query.where(ProgramaMateria.materia_id == materia_id)
        if carrera_id is not None:
            query = query.where(ProgramaMateria.carrera_id == carrera_id)
        if cohorte_id is not None:
            query = query.where(ProgramaMateria.cohorte_id == cohorte_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_clave(
        self,
        *,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
    ) -> ProgramaMateria | None:
        result = await self.session.execute(
            self._base_query().where(
                ProgramaMateria.materia_id == materia_id,
                ProgramaMateria.carrera_id == carrera_id,
                ProgramaMateria.cohorte_id == cohorte_id,
            )
        )
        return result.scalar_one_or_none()


class FechaAcademicaRepository(BaseRepository[FechaAcademica]):
    model = FechaAcademica

    async def list_filtered(
        self,
        *,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        tipo: TipoEvaluacion | None = None,
        periodo: str | None = None,
    ) -> Sequence[FechaAcademica]:
        query = self._base_query().order_by(FechaAcademica.fecha, FechaAcademica.numero)
        if materia_id is not None:
            query = query.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            query = query.where(FechaAcademica.cohorte_id == cohorte_id)
        if tipo is not None:
            query = query.where(FechaAcademica.tipo == tipo)
        if periodo is not None:
            query = query.where(FechaAcademica.periodo == periodo)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_calendario(
        self,
        *,
        desde: date,
        hasta: date,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
    ) -> Sequence[FechaAcademica]:
        query = (
            self._base_query()
            .where(FechaAcademica.fecha >= desde)
            .where(FechaAcademica.fecha <= hasta)
            .order_by(FechaAcademica.fecha)
        )
        if materia_id is not None:
            query = query.where(FechaAcademica.materia_id == materia_id)
        if cohorte_id is not None:
            query = query.where(FechaAcademica.cohorte_id == cohorte_id)
        result = await self.session.execute(query)
        return result.scalars().all()
