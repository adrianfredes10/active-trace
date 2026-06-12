"""Servicio de estructura académica (C-06)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.repositories.estructura_repository import (
    CarreraRepository,
    CohorteRepository,
    MateriaRepository,
)
from app.schemas.estructura import (
    CarreraCreate,
    CarreraUpdate,
    CohorteCreate,
    CohorteUpdate,
    MateriaCreate,
    MateriaUpdate,
)


class EstructuraService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.carreras = CarreraRepository(session, tenant_id)
        self.cohortes = CohorteRepository(session, tenant_id)
        self.materias = MateriaRepository(session, tenant_id)

    async def list_carreras(self) -> list[Carrera]:
        return await self.carreras.list_all()

    async def create_carrera(self, data: CarreraCreate) -> Carrera:
        if await self.carreras.get_by_codigo(data.codigo):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una carrera con ese código",
            )
        return await self.carreras.add(
            Carrera(
                codigo=data.codigo,
                nombre=data.nombre,
                estado=data.estado,
            )
        )

    async def update_carrera(
        self,
        carrera_id: uuid.UUID,
        data: CarreraUpdate,
    ) -> Carrera:
        carrera = await self._get_carrera(carrera_id)
        if data.nombre is not None:
            carrera.nombre = data.nombre
        if data.estado is not None:
            carrera.estado = data.estado
        await self.session.flush()
        return carrera

    async def delete_carrera(self, carrera_id: uuid.UUID) -> None:
        carrera = await self._get_carrera(carrera_id)
        await self.carreras.soft_delete(carrera)

    async def list_cohortes(self, *, carrera_id: uuid.UUID | None = None) -> list[Cohorte]:
        if carrera_id is not None:
            await self._get_carrera(carrera_id)
        return await self.cohortes.list_all(carrera_id=carrera_id)

    async def create_cohorte(self, data: CohorteCreate) -> Cohorte:
        carrera = await self._get_carrera(data.carrera_id)
        if carrera.estado == EntidadEstado.INACTIVA:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La carrera está inactiva; no admite cohortes nuevas",
            )
        if data.vig_hasta is not None and data.vig_hasta < data.vig_desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="vig_hasta no puede ser anterior a vig_desde",
            )
        if await self.cohortes.get_by_nombre(
            carrera_id=data.carrera_id,
            nombre=data.nombre,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cohorte con ese nombre en la carrera",
            )
        return await self.cohortes.add(
            Cohorte(
                carrera_id=data.carrera_id,
                nombre=data.nombre,
                anio=data.anio,
                vig_desde=data.vig_desde,
                vig_hasta=data.vig_hasta,
                estado=data.estado,
            )
        )

    async def update_cohorte(
        self,
        cohorte_id: uuid.UUID,
        data: CohorteUpdate,
    ) -> Cohorte:
        cohorte = await self._get_cohorte(cohorte_id)
        if data.nombre is not None and data.nombre != cohorte.nombre:
            if await self.cohortes.get_by_nombre(
                carrera_id=cohorte.carrera_id,
                nombre=data.nombre,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Ya existe una cohorte con ese nombre en la carrera",
                )
            cohorte.nombre = data.nombre
        if data.anio is not None:
            cohorte.anio = data.anio
        if data.vig_desde is not None:
            cohorte.vig_desde = data.vig_desde
        if data.vig_hasta is not None:
            cohorte.vig_hasta = data.vig_hasta
        if data.estado is not None:
            cohorte.estado = data.estado
        vig_desde = cohorte.vig_desde
        vig_hasta = cohorte.vig_hasta
        if vig_hasta is not None and vig_hasta < vig_desde:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="vig_hasta no puede ser anterior a vig_desde",
            )
        await self.session.flush()
        return cohorte

    async def delete_cohorte(self, cohorte_id: uuid.UUID) -> None:
        cohorte = await self._get_cohorte(cohorte_id)
        await self.cohortes.soft_delete(cohorte)

    async def list_materias(self) -> list[Materia]:
        return await self.materias.list_all()

    async def create_materia(self, data: MateriaCreate) -> Materia:
        if await self.materias.get_by_codigo(data.codigo):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una materia con ese código",
            )
        return await self.materias.add(
            Materia(
                codigo=data.codigo,
                nombre=data.nombre,
                estado=data.estado,
            )
        )

    async def update_materia(
        self,
        materia_id: uuid.UUID,
        data: MateriaUpdate,
    ) -> Materia:
        materia = await self._get_materia(materia_id)
        if data.nombre is not None:
            materia.nombre = data.nombre
        if data.estado is not None:
            materia.estado = data.estado
        await self.session.flush()
        return materia

    async def delete_materia(self, materia_id: uuid.UUID) -> None:
        materia = await self._get_materia(materia_id)
        await self.materias.soft_delete(materia)

    async def _get_carrera(self, carrera_id: uuid.UUID) -> Carrera:
        carrera = await self.carreras.get(carrera_id)
        if carrera is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carrera no encontrada",
            )
        return carrera

    async def _get_cohorte(self, cohorte_id: uuid.UUID) -> Cohorte:
        cohorte = await self.cohortes.get(cohorte_id)
        if cohorte is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cohorte no encontrada",
            )
        return cohorte

    async def _get_materia(self, materia_id: uuid.UUID) -> Materia:
        materia = await self.materias.get(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Materia no encontrada",
            )
        return materia
