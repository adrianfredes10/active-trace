"""Servicio de encuentros — C-13."""

import html
import uuid
from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.encuentro import (
    EstadoInstanciaEncuentro,
    InstanciaEncuentro,
    SlotEncuentro,
)
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.encuentro_repository import (
    InstanciaEncuentroRepository,
    SlotEncuentroRepository,
)
from app.services.encuentro_rules import generar_fechas_recurrente

_ROLES_AMPLIOS = frozenset({"COORDINADOR", "ADMIN"})


class EncuentroService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._slots = SlotEncuentroRepository(session, tenant_id)
        self._instancias = InstanciaEncuentroRepository(session, tenant_id)
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

    async def crear_recurrente(
        self,
        *,
        user: CurrentUser,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        titulo: str,
        hora: time,
        dia_semana,
        fecha_inicio: date,
        cant_semanas: int,
        meet_url: str | None,
        vig_desde: date,
        vig_hasta: date | None,
    ) -> tuple[SlotEncuentro, list[InstanciaEncuentro]]:
        await self._verificar_asignacion(asignacion_id, user)
        fechas = generar_fechas_recurrente(fecha_inicio, dia_semana, cant_semanas)
        slot = SlotEncuentro(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            titulo=titulo,
            hora=hora,
            dia_semana=dia_semana,
            fecha_inicio=fecha_inicio,
            cant_semanas=cant_semanas,
            meet_url=meet_url,
            vig_desde=vig_desde,
            vig_hasta=vig_hasta,
        )
        await self._slots.add(slot)
        instancias = [
            InstanciaEncuentro(
                slot_id=slot.id,
                materia_id=materia_id,
                fecha=f,
                hora=hora,
                titulo=titulo,
                meet_url=meet_url,
                estado=EstadoInstanciaEncuentro.programado,
            )
            for f in fechas
        ]
        for inst in instancias:
            await self._instancias.add(inst)
        return slot, instancias

    async def crear_unico(
        self,
        *,
        user: CurrentUser,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        titulo: str,
        fecha: date,
        hora: time,
        meet_url: str | None,
    ) -> InstanciaEncuentro:
        await self._verificar_asignacion(asignacion_id, user)
        slot = SlotEncuentro(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            titulo=titulo,
            hora=hora,
            fecha_unica=fecha,
            cant_semanas=0,
            meet_url=meet_url,
            vig_desde=fecha,
        )
        await self._slots.add(slot)
        instancia = InstanciaEncuentro(
            slot_id=slot.id,
            materia_id=materia_id,
            fecha=fecha,
            hora=hora,
            titulo=titulo,
            meet_url=meet_url,
            estado=EstadoInstanciaEncuentro.programado,
        )
        await self._instancias.add(instancia)
        return instancia

    async def actualizar_instancia(
        self,
        instancia_id: uuid.UUID,
        *,
        user: CurrentUser,
        estado: EstadoInstanciaEncuentro | None = None,
        meet_url: str | None = None,
        video_url: str | None = None,
        comentario: str | None = None,
    ) -> InstanciaEncuentro:
        instancia = await self._instancias.get(instancia_id)
        if instancia is None:
            raise ValueError("Instancia no encontrada")
        if estado is not None:
            instancia.estado = estado
        if meet_url is not None:
            instancia.meet_url = meet_url
        if video_url is not None:
            instancia.video_url = video_url
        if comentario is not None:
            instancia.comentario = comentario
        await self._session.flush()
        return instancia

    async def listar_por_materia(
        self, materia_id: uuid.UUID, *, desde: date | None = None
    ) -> list[InstanciaEncuentro]:
        return list(await self._instancias.list_by_materia(materia_id, desde=desde))

    async def listar_admin(self, user: CurrentUser) -> list[InstanciaEncuentro]:
        if not _ROLES_AMPLIOS.intersection(user.roles):
            raise PermissionError("Requiere rol COORDINADOR o ADMIN")
        return list(await self._instancias.list_tenant())

    def generar_html(self, instancias: list[InstanciaEncuentro]) -> str:
        filas = []
        for inst in instancias:
            filas.append(
                "<tr>"
                f"<td>{html.escape(inst.fecha.isoformat())}</td>"
                f"<td>{html.escape(inst.hora.strftime('%H:%M'))}</td>"
                f"<td>{html.escape(inst.titulo)}</td>"
                f"<td>{html.escape(inst.estado.value)}</td>"
                f"<td>{html.escape(inst.meet_url or '')}</td>"
                "</tr>"
            )
        cuerpo = "".join(filas) or "<tr><td colspan='5'>Sin encuentros</td></tr>"
        return (
            "<table border='1' cellpadding='4'>"
            "<thead><tr><th>Fecha</th><th>Hora</th><th>Título</th>"
            "<th>Estado</th><th>Enlace</th></tr></thead>"
            f"<tbody>{cuerpo}</tbody></table>"
        )
