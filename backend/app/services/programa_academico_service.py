"""Servicios de programas y fechas académicas — C-17."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion import TipoEvaluacion
from app.models.programa_academico import FechaAcademica, ProgramaMateria
from app.repositories.estructura_repository import CohorteRepository, MateriaRepository
from app.repositories.programa_academico_repository import (
    FechaAcademicaRepository,
    ProgramaMateriaRepository,
)
from app.services.fecha_academica_html import generar_html_fechas
from app.services.programa_storage import generar_referencia_archivo


class ProgramaService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = ProgramaMateriaRepository(session, tenant_id)
        self._materias = MateriaRepository(session, tenant_id)

    async def asociar(
        self,
        *,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        titulo: str,
        nombre_archivo: str,
    ) -> ProgramaMateria:
        materia = await self._materias.get(materia_id)
        if materia is None:
            raise ValueError("Materia no encontrada")
        ref = generar_referencia_archivo(self._tenant_id, nombre_archivo)
        existente = await self._repo.get_by_clave(
            materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id
        )
        if existente is not None:
            existente.titulo = titulo
            existente.referencia_archivo = ref
            existente.cargado_at = datetime.now(timezone.utc)
            await self._session.flush()
            return existente
        return await self._repo.add(
            ProgramaMateria(
                materia_id=materia_id,
                carrera_id=carrera_id,
                cohorte_id=cohorte_id,
                titulo=titulo,
                referencia_archivo=ref,
                cargado_at=datetime.now(timezone.utc),
            )
        )

    async def listar(
        self,
        *,
        materia_id: uuid.UUID | None = None,
        carrera_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
    ) -> list[ProgramaMateria]:
        return list(
            await self._repo.list_filtered(
                materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id
            )
        )

    async def obtener(self, programa_id: uuid.UUID) -> ProgramaMateria:
        programa = await self._repo.get(programa_id)
        if programa is None:
            raise ValueError("Programa no encontrado")
        return programa

    async def eliminar(self, programa_id: uuid.UUID) -> None:
        programa = await self.obtener(programa_id)
        await self._repo.soft_delete(programa)


class FechaAcademicaService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = FechaAcademicaRepository(session, tenant_id)
        self._materias = MateriaRepository(session, tenant_id)
        self._cohortes = CohorteRepository(session, tenant_id)

    async def crear(
        self,
        *,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        tipo: TipoEvaluacion,
        numero: int,
        periodo: str,
        fecha: date,
        titulo: str,
    ) -> FechaAcademica:
        if numero < 1:
            raise ValueError("El número de instancia debe ser >= 1")
        if await self._materias.get(materia_id) is None:
            raise ValueError("Materia no encontrada")
        if await self._cohortes.get(cohorte_id) is None:
            raise ValueError("Cohorte no encontrada")
        return await self._repo.add(
            FechaAcademica(
                materia_id=materia_id,
                cohorte_id=cohorte_id,
                tipo=tipo,
                numero=numero,
                periodo=periodo,
                fecha=fecha,
                titulo=titulo,
            )
        )

    async def actualizar(
        self,
        fecha_id: uuid.UUID,
        *,
        tipo: TipoEvaluacion | None = None,
        numero: int | None = None,
        periodo: str | None = None,
        fecha: date | None = None,
        titulo: str | None = None,
    ) -> FechaAcademica:
        entity = await self._repo.get(fecha_id)
        if entity is None:
            raise ValueError("Fecha académica no encontrada")
        if tipo is not None:
            entity.tipo = tipo
        if numero is not None:
            if numero < 1:
                raise ValueError("El número de instancia debe ser >= 1")
            entity.numero = numero
        if periodo is not None:
            entity.periodo = periodo
        if fecha is not None:
            entity.fecha = fecha
        if titulo is not None:
            entity.titulo = titulo
        await self._session.flush()
        return entity

    async def eliminar(self, fecha_id: uuid.UUID) -> None:
        entity = await self._repo.get(fecha_id)
        if entity is None:
            raise ValueError("Fecha académica no encontrada")
        await self._repo.soft_delete(entity)

    async def listar(
        self,
        *,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        tipo: TipoEvaluacion | None = None,
        periodo: str | None = None,
    ) -> list[FechaAcademica]:
        return list(
            await self._repo.list_filtered(
                materia_id=materia_id,
                cohorte_id=cohorte_id,
                tipo=tipo,
                periodo=periodo,
            )
        )

    async def calendario(
        self,
        *,
        desde: date,
        hasta: date,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
    ) -> list[FechaAcademica]:
        if desde > hasta:
            raise ValueError("Rango de fechas inválido")
        return list(
            await self._repo.list_calendario(
                desde=desde, hasta=hasta, materia_id=materia_id, cohorte_id=cohorte_id
            )
        )

    async def html_aula(
        self, *, materia_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> str:
        materia = await self._materias.get(materia_id)
        if materia is None:
            raise ValueError("Materia no encontrada")
        fechas = await self._repo.list_filtered(
            materia_id=materia_id, cohorte_id=cohorte_id
        )
        return generar_html_fechas(list(fechas), materia_nombre=materia.nombre)
