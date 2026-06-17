"""Servicio de tareas internas — C-16."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.tarea import ComentarioTarea, EstadoTarea, Tarea
from app.repositories.tarea_repository import ComentarioTareaRepository, TareaRepository
from app.services.tarea_rules import puede_transicionar

_ROLES_ADMIN = frozenset({"COORDINADOR", "ADMIN"})


class TareaService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._tareas = TareaRepository(session, tenant_id)
        self._comentarios = ComentarioTareaRepository(session, tenant_id)

    def _es_admin(self, user: CurrentUser) -> bool:
        return bool(_ROLES_ADMIN.intersection(user.roles))

    async def _obtener_con_acceso(
        self, tarea_id: uuid.UUID, user: CurrentUser
    ) -> Tarea:
        tarea = await self._tareas.get(tarea_id)
        if tarea is None:
            raise ValueError("Tarea no encontrada")
        if self._es_admin(user):
            return tarea
        if user.id not in (tarea.asignado_a, tarea.asignado_por):
            raise PermissionError("Sin acceso a esta tarea")
        return tarea

    async def crear(
        self,
        *,
        user: CurrentUser,
        asignado_a: uuid.UUID,
        descripcion: str,
        materia_id: uuid.UUID | None = None,
        contexto_id: uuid.UUID | None = None,
    ) -> Tarea:
        return await self._tareas.add(
            Tarea(
                materia_id=materia_id,
                asignado_a=asignado_a,
                asignado_por=user.id,
                descripcion=descripcion,
                contexto_id=contexto_id,
                estado=EstadoTarea.pendiente,
            )
        )

    async def listar_mias(self, user: CurrentUser) -> list[Tarea]:
        return list(await self._tareas.list_mias(user.id))

    async def listar_admin(
        self,
        user: CurrentUser,
        *,
        asignado_a: uuid.UUID | None = None,
        asignado_por: uuid.UUID | None = None,
        materia_id: uuid.UUID | None = None,
        estado: EstadoTarea | None = None,
        busqueda: str | None = None,
    ) -> list[Tarea]:
        if not self._es_admin(user):
            raise PermissionError("Solo coordinación puede listar todas las tareas")
        return list(
            await self._tareas.list_admin(
                asignado_a=asignado_a,
                asignado_por=asignado_por,
                materia_id=materia_id,
                estado=estado,
                busqueda=busqueda,
            )
        )

    async def cambiar_estado(
        self, tarea_id: uuid.UUID, *, user: CurrentUser, estado: EstadoTarea
    ) -> Tarea:
        tarea = await self._obtener_con_acceso(tarea_id, user)
        if not puede_transicionar(tarea.estado, estado):
            raise ValueError(f"Transición inválida: {tarea.estado.value} → {estado.value}")
        tarea.estado = estado
        await self._session.flush()
        return tarea

    async def delegar(
        self,
        tarea_id: uuid.UUID,
        *,
        user: CurrentUser,
        nuevo_asignado: uuid.UUID,
    ) -> Tarea:
        tarea = await self._obtener_con_acceso(tarea_id, user)
        if tarea.asignado_a != user.id and not self._es_admin(user):
            raise PermissionError("Solo el asignado actual puede delegar")
        if nuevo_asignado == tarea.asignado_a:
            raise ValueError("El usuario ya está asignado")
        tarea.asignado_por = user.id
        tarea.asignado_a = nuevo_asignado
        if tarea.estado == EstadoTarea.resuelta:
            tarea.estado = EstadoTarea.pendiente
        await self._session.flush()
        return tarea

    async def agregar_comentario(
        self, tarea_id: uuid.UUID, *, user: CurrentUser, texto: str
    ) -> ComentarioTarea:
        await self._obtener_con_acceso(tarea_id, user)
        return await self._comentarios.add(
            ComentarioTarea(
                tarea_id=tarea_id,
                autor_id=user.id,
                texto=texto,
                creado_at=datetime.now(timezone.utc),
            )
        )

    async def listar_comentarios(
        self, tarea_id: uuid.UUID, user: CurrentUser
    ) -> list[ComentarioTarea]:
        await self._obtener_con_acceso(tarea_id, user)
        return list(await self._comentarios.list_by_tarea(tarea_id))
