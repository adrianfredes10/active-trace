"""Worker de despacho de comunicaciones — C-12."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.mail_sender import MailDeliveryError, MailSender
from app.models.comunicacion import EstadoComunicacion
from app.models.tenant import Tenant
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.services.comunicacion_rules import listo_para_despacho, validar_transicion

logger = logging.getLogger(__name__)


async def _tenant_requiere_aprobacion(session: AsyncSession, tenant_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(Tenant.aprobacion_masiva_comunicaciones).where(
            Tenant.id == tenant_id,
            Tenant.deleted_at.is_(None),
        )
    )
    valor = result.scalar_one_or_none()
    return True if valor is None else bool(valor)


async def procesar_pendientes(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    mailer: MailSender | None = None,
    limit: int = 50,
) -> int:
    """Despacha comunicaciones Pendiente listas (RN-15). Retorna cantidad procesada."""
    repo = ComunicacionRepository(session, tenant_id)
    sender = mailer or MailSender()
    requiere_aprobacion = await _tenant_requiere_aprobacion(session, tenant_id)
    pendientes = await repo.list_pendientes_despacho(limit=limit)
    procesadas = 0

    for item in pendientes:
        if not listo_para_despacho(
            aprobado=item.aprobado,
            es_masivo=item.es_masivo,
            requiere_aprobacion=requiere_aprobacion,
        ):
            continue
        try:
            validar_transicion(item.estado, EstadoComunicacion.enviando)
            item.estado = EstadoComunicacion.enviando
            await session.flush()
            await sender.send(
                destinatario=item.destinatario,
                asunto=item.asunto,
                cuerpo=item.cuerpo,
            )
            validar_transicion(item.estado, EstadoComunicacion.enviado)
            item.estado = EstadoComunicacion.enviado
            item.enviado_at = datetime.now(timezone.utc)
            item.error_detalle = None
        except MailDeliveryError as exc:
            validar_transicion(item.estado, EstadoComunicacion.error)
            item.estado = EstadoComunicacion.error
            item.error_detalle = str(exc)[:500]
        await session.flush()
        procesadas += 1

    if procesadas:
        logger.info("worker comunicaciones tenant=%s procesadas=%s", tenant_id, procesadas)
    return procesadas
