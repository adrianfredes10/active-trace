"""Servicio de bandeja de mensajes internos — C-20 (FL-10)."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mensaje_interno import HiloMensaje, MensajeInterno
from app.repositories.inbox_repository import (
    HiloMensajeRepository,
    MensajeInternoRepository,
)
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.inbox import (
    HiloDetalleResponse,
    HiloListResponse,
    HiloResumen,
    MensajeCreadoResponse,
    MensajeResponse,
)

logger = logging.getLogger(__name__)


class InboxService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._hilos = HiloMensajeRepository(session, tenant_id)
        self._mensajes = MensajeInternoRepository(session, tenant_id)
        self._usuarios = UsuarioRepository(session, tenant_id)

    async def enviar_mensaje(
        self,
        *,
        remitente_id: uuid.UUID,
        destinatario_id: uuid.UUID,
        asunto: str,
        cuerpo: str,
    ) -> MensajeCreadoResponse:
        if remitente_id == destinatario_id:
            raise ValueError("No podés enviarte un mensaje a vos mismo")
        destinatario = await self._usuarios.get(destinatario_id)
        if destinatario is None:
            raise ValueError("Destinatario no encontrado")
        ahora = datetime.now(timezone.utc)
        hilo = await self._hilos.create_hilo(
            asunto=asunto,
            participante_a_id=remitente_id,
            participante_b_id=destinatario_id,
            iniciado_por_id=remitente_id,
            ultimo_mensaje_at=ahora,
        )
        mensaje = await self._mensajes.add_mensaje(
            hilo_id=hilo.id,
            autor_id=remitente_id,
            cuerpo=cuerpo,
            enviado_at=ahora,
        )
        logger.info("mensaje interno creado hilo_id=%s", hilo.id)
        return MensajeCreadoResponse(hilo_id=hilo.id, mensaje_id=mensaje.id)

    async def listar_hilos(self, usuario_id: uuid.UUID) -> HiloListResponse:
        hilos = await self._hilos.list_for_usuario(usuario_id)
        items: list[HiloResumen] = []
        for hilo in hilos:
            otro = (
                hilo.participante_b_id
                if hilo.participante_a_id == usuario_id
                else hilo.participante_a_id
            )
            count = await self._mensajes.count_by_hilo(hilo.id)
            items.append(
                HiloResumen(
                    id=hilo.id,
                    asunto=hilo.asunto,
                    otro_participante_id=otro,
                    ultimo_mensaje_at=hilo.ultimo_mensaje_at,
                    mensajes_count=count,
                )
            )
        return HiloListResponse(items=items)

    async def obtener_hilo(
        self, hilo_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> HiloDetalleResponse | None:
        hilo = await self._hilos.get_for_participant(hilo_id, usuario_id)
        if hilo is None:
            return None
        mensajes = await self._mensajes.list_by_hilo(hilo_id)
        return self._to_detalle(hilo, mensajes)

    async def responder(
        self, hilo_id: uuid.UUID, usuario_id: uuid.UUID, cuerpo: str
    ) -> MensajeResponse | None:
        hilo = await self._hilos.get_for_participant(hilo_id, usuario_id)
        if hilo is None:
            return None
        ahora = datetime.now(timezone.utc)
        mensaje = await self._mensajes.add_mensaje(
            hilo_id=hilo_id,
            autor_id=usuario_id,
            cuerpo=cuerpo,
            enviado_at=ahora,
        )
        hilo.ultimo_mensaje_at = ahora
        await self._session.flush()
        logger.info("respuesta interna hilo_id=%s", hilo_id)
        return MensajeResponse(
            id=mensaje.id,
            autor_id=mensaje.autor_id,
            cuerpo=mensaje.cuerpo,
            enviado_at=mensaje.enviado_at,
        )

    @staticmethod
    def _to_detalle(
        hilo: HiloMensaje, mensajes: list[MensajeInterno]
    ) -> HiloDetalleResponse:
        return HiloDetalleResponse(
            id=hilo.id,
            asunto=hilo.asunto,
            participante_a_id=hilo.participante_a_id,
            participante_b_id=hilo.participante_b_id,
            mensajes=[
                MensajeResponse(
                    id=m.id,
                    autor_id=m.autor_id,
                    cuerpo=m.cuerpo,
                    enviado_at=m.enviado_at,
                )
                for m in mensajes
            ],
        )
