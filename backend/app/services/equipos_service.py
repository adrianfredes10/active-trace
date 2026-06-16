"""Servicio de equipos docentes — C-08.

Operaciones sobre Asignacion agrupadas por equipo (materia × carrera × cohorte):
mis-equipos, asignación masiva, clonado, vigencia en bloque y exportación.
"""

import csv
import io
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.schemas.asignacion import AsignacionCreate
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    ClonarEquipoRequest,
    ModificarVigenciaEquipoRequest,
)
from app.services.asignacion_service import AsignacionService

logger = logging.getLogger(__name__)


class EquiposService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = AsignacionRepository(session, tenant_id)
        self._asig_svc = AsignacionService(session, tenant_id)

    async def mis_equipos(
        self,
        usuario_id: uuid.UUID,
        *,
        solo_vigentes: bool = True,
    ) -> list[Asignacion]:
        return list(
            await self._repo.list_by_usuario(usuario_id, solo_vigentes=solo_vigentes)
        )

    async def asignacion_masiva(
        self, data: AsignacionMasivaRequest
    ) -> list[Asignacion]:
        rol = data.rol
        creadas: list[Asignacion] = []
        for usuario_id in data.usuario_ids:
            asig = await self._asig_svc.crear_asignacion(
                AsignacionCreate(
                    usuario_id=usuario_id,
                    rol=rol,
                    materia_id=data.materia_id,
                    carrera_id=data.carrera_id,
                    cohorte_id=data.cohorte_id,
                    comisiones=data.comisiones,
                    desde=data.desde,
                    hasta=data.hasta,
                )
            )
            creadas.append(asig)
        logger.info("asignacion masiva: %s registros", len(creadas))
        return creadas

    async def clonar_equipo(self, data: ClonarEquipoRequest) -> list[Asignacion]:
        origen = await self._repo.list_by_equipo(
            materia_id=data.origen.materia_id,
            carrera_id=data.origen.carrera_id,
            cohorte_id=data.origen.cohorte_id,
        )
        if not origen:
            return []

        clonadas: list[Asignacion] = []
        for src in origen:
            asig = await self._asig_svc.crear_asignacion(
                AsignacionCreate(
                    usuario_id=src.usuario_id,
                    rol=src.rol,
                    materia_id=data.destino.materia_id,
                    carrera_id=data.destino.carrera_id,
                    cohorte_id=data.destino.cohorte_id,
                    comisiones=src.comisiones or [],
                    responsable_id=src.responsable_id,
                    desde=data.desde,
                    hasta=data.hasta,
                )
            )
            clonadas.append(asig)
        logger.info("equipo clonado: %s asignaciones", len(clonadas))
        return clonadas

    async def modificar_vigencia_equipo(
        self, data: ModificarVigenciaEquipoRequest
    ) -> list[Asignacion]:
        if data.hasta is not None and data.hasta < data.desde:
            raise ValueError("'hasta' no puede ser anterior a 'desde'")

        equipo = await self._repo.list_by_equipo(
            materia_id=data.materia_id,
            carrera_id=data.carrera_id,
            cohorte_id=data.cohorte_id,
        )
        actualizadas: list[Asignacion] = []
        for asig in equipo:
            asig.desde = data.desde
            asig.hasta = data.hasta
            actualizadas.append(asig)
        await self._session.flush()
        logger.info("vigencia equipo actualizada: %s asignaciones", len(actualizadas))
        return actualizadas

    async def exportar_equipo_csv(
        self,
        *,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
    ) -> str:
        equipo = await self._repo.list_by_equipo(
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
        )
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "usuario_id",
                "rol",
                "materia_id",
                "carrera_id",
                "cohorte_id",
                "comisiones",
                "desde",
                "hasta",
                "vigente",
            ]
        )
        for a in equipo:
            writer.writerow(
                [
                    str(a.usuario_id),
                    a.rol.value,
                    str(a.materia_id) if a.materia_id else "",
                    str(a.carrera_id) if a.carrera_id else "",
                    str(a.cohorte_id) if a.cohorte_id else "",
                    ",".join(a.comisiones or []),
                    a.desde.isoformat(),
                    a.hasta.isoformat() if a.hasta else "",
                    "si" if a.vigente else "no",
                ]
            )
        return buffer.getvalue()
