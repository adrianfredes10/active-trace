"""Servicio del panel de auditoría y métricas — C-19 (F9.1, F9.2)."""

import uuid
from datetime import datetime, time, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.asignacion import RolAsignacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.comunicacion_repository import ComunicacionRepository

_ROLES_GLOBAL = frozenset({"ADMIN", "FINANZAS"})
_DEFAULT_LIMIT = 200
_MAX_LIMIT = 500


class AuditoriaPanelService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._audit = AuditLogRepository(session, tenant_id)
        self._comunicaciones = ComunicacionRepository(session, tenant_id)
        self._asignaciones = AsignacionRepository(session, tenant_id)

    async def _scope_materias(
        self, user: CurrentUser
    ) -> tuple[set[uuid.UUID] | None, uuid.UUID]:
        if _ROLES_GLOBAL.intersection(user.roles):
            return None, user.id
        asignaciones = await self._asignaciones.list_vigentes_by_usuario(user.id)
        materias = {
            a.materia_id
            for a in asignaciones
            if a.materia_id is not None and a.rol == RolAsignacion.coordinador
        }
        return materias, user.id

    @staticmethod
    def _clamp_limit(limit: int) -> int:
        return max(1, min(limit, _MAX_LIMIT))

    async def acciones_por_dia(
        self,
        user: CurrentUser,
        *,
        desde: datetime,
        hasta: datetime,
    ) -> list:
        materia_ids, actor_scope = await self._scope_materias(user)
        return await self._audit.acciones_por_dia(
            desde=desde,
            hasta=hasta,
            materia_ids=materia_ids,
            actor_scope=actor_scope,
        )

    async def comunicaciones_por_docente(self, user: CurrentUser) -> list:
        materia_ids, _ = await self._scope_materias(user)
        return await self._comunicaciones.estados_por_docente(materia_ids=materia_ids)

    async def interacciones(
        self,
        user: CurrentUser,
        *,
        desde: datetime,
        hasta: datetime,
    ) -> list:
        materia_ids, actor_scope = await self._scope_materias(user)
        return await self._audit.interacciones_agrupadas(
            desde=desde,
            hasta=hasta,
            materia_ids=materia_ids,
            actor_scope=actor_scope,
        )

    async def log_completo(
        self,
        user: CurrentUser,
        *,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        materia_id: uuid.UUID | None = None,
        usuario_id: uuid.UUID | None = None,
        accion: str | None = None,
        limit: int = _DEFAULT_LIMIT,
    ) -> list:
        materia_ids, actor_scope = await self._scope_materias(user)
        return list(
            await self._audit.list_filtered(
                desde=desde,
                hasta=hasta,
                materia_id=materia_id,
                actor_id=usuario_id,
                accion=accion,
                materia_ids=materia_ids,
                actor_scope=actor_scope,
                limit=self._clamp_limit(limit),
            )
        )

    @staticmethod
    def rango_dia(desde: datetime, hasta: datetime) -> tuple[datetime, datetime]:
        if desde > hasta:
            raise ValueError("Rango de fechas inválido")
        return desde, hasta

    @staticmethod
    def default_rango() -> tuple[datetime, datetime]:
        hoy = datetime.now(timezone.utc).date()
        inicio = datetime.combine(hoy.replace(day=1), time.min, tzinfo=timezone.utc)
        fin = datetime.now(timezone.utc)
        return inicio, fin
