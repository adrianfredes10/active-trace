"""Servicio de guardias — C-13."""

import csv
import io
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.encuentro import EstadoGuardia, Guardia
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.guardia_repository import GuardiaRepository

_ROLES_AMPLIOS = frozenset({"COORDINADOR", "ADMIN"})


class GuardiaService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = GuardiaRepository(session, tenant_id)
        self._asignaciones = AsignacionRepository(session, tenant_id)

    async def _verificar_asignacion(
        self, asignacion_id: uuid.UUID, user: CurrentUser
    ) -> None:
        asignacion = await self._asignaciones.get(asignacion_id)
        if asignacion is None:
            raise ValueError("Asignación no encontrada")
        if not _ROLES_AMPLIOS.intersection(user.roles):
            if asignacion.usuario_id != user.id:
                raise PermissionError("Sin acceso a esta asignación")

    async def registrar(
        self,
        *,
        user: CurrentUser,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        carrera_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        dia,
        horario: str,
        comentarios: str | None,
    ) -> Guardia:
        await self._verificar_asignacion(asignacion_id, user)
        guardia = Guardia(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            carrera_id=carrera_id,
            cohorte_id=cohorte_id,
            dia=dia,
            horario=horario,
            comentarios=comentarios,
            estado=EstadoGuardia.pendiente,
            creada_at=datetime.now(timezone.utc),
        )
        return await self._repo.add(guardia)

    async def listar(
        self,
        user: CurrentUser,
        *,
        materia_id: uuid.UUID | None = None,
        cohorte_id: uuid.UUID | None = None,
        asignacion_id: uuid.UUID | None = None,
    ) -> list[Guardia]:
        if _ROLES_AMPLIOS.intersection(user.roles):
            return list(
                await self._repo.list_filtered(
                    materia_id=materia_id, cohorte_id=cohorte_id
                )
            )
        if asignacion_id is None:
            raise ValueError("asignacion_id requerido para tutores/docentes")
        await self._verificar_asignacion(asignacion_id, user)
        return list(await self._repo.list_by_asignacion(asignacion_id))

    async def actualizar(
        self, guardia_id: uuid.UUID, *, user: CurrentUser, estado, comentarios
    ) -> Guardia:
        guardia = await self._repo.get(guardia_id)
        if guardia is None:
            raise ValueError("Guardia no encontrada")
        await self._verificar_asignacion(guardia.asignacion_id, user)
        if estado is not None:
            guardia.estado = estado
        if comentarios is not None:
            guardia.comentarios = comentarios
        await self._session.flush()
        return guardia

    def exportar_csv(self, guardias: list[Guardia]) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["dia", "horario", "estado", "materia_id", "cohorte_id", "comentarios"]
        )
        for g in guardias:
            writer.writerow(
                [
                    g.dia.value,
                    g.horario,
                    g.estado.value,
                    str(g.materia_id),
                    str(g.cohorte_id),
                    g.comentarios or "",
                ]
            )
        return buffer.getvalue().encode("utf-8-sig")
