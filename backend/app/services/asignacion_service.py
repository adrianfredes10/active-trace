"""Servicio de asignaciones — C-07.

Reglas clave:
- El tenant_id lo provee siempre el contexto, nunca el body.
- Validación de vigencia antes de persistir (desde <= hasta si ambas presentes).
- Soft delete: anular_asignacion usa deleted_at, no hard delete.
"""

import logging
import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.schemas.asignacion import AsignacionCreate, AsignacionUpdate

logger = logging.getLogger(__name__)


class AsignacionService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = AsignacionRepository(session, tenant_id)

    async def crear_asignacion(self, data: AsignacionCreate) -> Asignacion:
        if data.hasta is not None and data.hasta < data.desde:
            raise ValueError("'hasta' no puede ser anterior a 'desde'")

        asig = Asignacion(
            usuario_id=data.usuario_id,
            rol=data.rol,
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
            comisiones=data.comisiones,
            responsable_id=data.responsable_id,
            desde=data.desde,
            hasta=data.hasta,
        )
        await self._repo.add(asig)
        logger.info("asignacion creada id=%s rol=%s", asig.id, asig.rol)
        return asig

    async def actualizar_vigencia(
        self, asignacion_id: uuid.UUID, data: AsignacionUpdate
    ) -> Asignacion | None:
        asig = await self._repo.get(asignacion_id)
        if asig is None:
            return None

        desde = data.desde if data.desde is not None else asig.desde
        hasta = data.hasta if data.hasta is not None else asig.hasta
        if hasta is not None and hasta < desde:
            raise ValueError("'hasta' no puede ser anterior a 'desde'")

        if data.rol is not None:
            asig.rol = data.rol
        if data.materia_id is not None:
            asig.materia_id = data.materia_id
        if data.carrera_id is not None:
            asig.carrera_id = data.carrera_id
        if data.cohorte_id is not None:
            asig.cohorte_id = data.cohorte_id
        if data.comisiones is not None:
            asig.comisiones = data.comisiones
        if data.responsable_id is not None:
            asig.responsable_id = data.responsable_id
        asig.desde = desde
        asig.hasta = hasta

        logger.info("asignacion actualizada id=%s", asignacion_id)
        return asig

    async def anular_asignacion(self, asignacion_id: uuid.UUID) -> bool:
        asig = await self._repo.get(asignacion_id)
        if asig is None:
            return False
        await self._repo.soft_delete(asig)
        logger.info("asignacion anulada id=%s", asignacion_id)
        return True

    async def get(self, asignacion_id: uuid.UUID) -> Asignacion | None:
        return await self._repo.get(asignacion_id)

    async def list_vigentes_by_usuario(
        self, usuario_id: uuid.UUID
    ) -> list[Asignacion]:
        return list(await self._repo.list_vigentes_by_usuario(usuario_id))

    async def list_vigentes_by_materia(
        self, materia_id: uuid.UUID
    ) -> list[Asignacion]:
        return list(await self._repo.list_vigentes_by_materia(materia_id))

    async def list_all(self) -> list[Asignacion]:
        return list(await self._repo.list())
