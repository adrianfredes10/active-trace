"""Servicio de comunicaciones salientes — C-12."""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.tenant import Tenant
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.services.comunicacion_rules import (
    TransicionInvalidaError,
    listo_para_despacho,
    requiere_aprobacion_masiva,
    validar_transicion,
)
from app.services.comunicacion_template import render_plantilla

logger = logging.getLogger(__name__)


class ComunicacionService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._repo = ComunicacionRepository(session, tenant_id)

    async def _tenant_requiere_aprobacion(self) -> bool:
        result = await self._session.execute(
            select(Tenant.aprobacion_masiva_comunicaciones).where(
                Tenant.id == self._tenant_id,
                Tenant.deleted_at.is_(None),
            )
        )
        valor = result.scalar_one_or_none()
        return True if valor is None else bool(valor)

    def preview(
        self, *, asunto: str, cuerpo: str, muestra: dict[str, str]
    ) -> dict[str, str]:
        variables = {
            "nombre": muestra["nombre"],
            "apellidos": muestra["apellidos"],
            "email": muestra["email"],
        }
        return {
            "asunto": render_plantilla(asunto, variables),
            "cuerpo": render_plantilla(cuerpo, variables),
        }

    async def encolar(
        self,
        *,
        user: CurrentUser,
        materia_id: uuid.UUID,
        asunto: str,
        cuerpo: str,
        destinatarios: list[dict[str, str]],
        confirmo_preview: bool,
    ) -> dict:
        if not confirmo_preview:
            raise ValueError("Debe confirmar la vista previa antes de enviar")

        es_masivo = requiere_aprobacion_masiva(len(destinatarios))
        tenant_requiere = await self._tenant_requiere_aprobacion()
        auto_aprobado = not (es_masivo and tenant_requiere)
        lote_id = uuid.uuid4()
        items: list[Comunicacion] = []

        for dest in destinatarios:
            variables = {
                "nombre": dest["nombre"],
                "apellidos": dest["apellidos"],
                "email": dest["email"],
            }
            items.append(
                Comunicacion(
                    enviado_por=user.id,
                    materia_id=materia_id,
                    destinatario=dest["email"],
                    asunto=render_plantilla(asunto, variables),
                    cuerpo=render_plantilla(cuerpo, variables),
                    estado=EstadoComunicacion.pendiente,
                    lote_id=lote_id,
                    es_masivo=es_masivo,
                    aprobado=auto_aprobado,
                )
            )

        guardadas = await self._repo.add_many(items)
        logger.info(
            "comunicaciones encoladas lote=%s count=%s masivo=%s",
            lote_id,
            len(guardadas),
            es_masivo,
        )
        return {
            "lote_id": lote_id,
            "encoladas": len(guardadas),
            "requiere_aprobacion": es_masivo and tenant_requiere,
            "items": guardadas,
        }

    async def aprobar_lote(self, lote_id: uuid.UUID, aprobador: CurrentUser) -> int:
        items = list(await self._repo.list_by_lote(lote_id))
        if not items:
            raise ValueError("Lote no encontrado")
        ahora = datetime.now(timezone.utc)
        count = 0
        for item in items:
            if item.estado != EstadoComunicacion.pendiente:
                continue
            if item.aprobado:
                continue
            item.aprobado = True
            item.aprobado_por = aprobador.id
            item.aprobado_at = ahora
            count += 1
        await self._session.flush()
        return count

    async def aprobar_individual(
        self, comunicacion_id: uuid.UUID, aprobador: CurrentUser
    ) -> Comunicacion:
        item = await self._repo.get(comunicacion_id)
        if item is None:
            raise ValueError("Comunicación no encontrada")
        if item.estado != EstadoComunicacion.pendiente:
            raise ValueError("Solo se aprueban comunicaciones pendientes")
        item.aprobado = True
        item.aprobado_por = aprobador.id
        item.aprobado_at = datetime.now(timezone.utc)
        await self._session.flush()
        return item

    async def cancelar(self, comunicacion_id: uuid.UUID) -> Comunicacion:
        item = await self._repo.get(comunicacion_id)
        if item is None:
            raise ValueError("Comunicación no encontrada")
        validar_transicion(item.estado, EstadoComunicacion.cancelado)
        item.estado = EstadoComunicacion.cancelado
        await self._session.flush()
        return item

    async def cancelar_lote(self, lote_id: uuid.UUID) -> int:
        items = list(await self._repo.list_by_lote(lote_id))
        count = 0
        for item in items:
            if item.estado != EstadoComunicacion.pendiente:
                continue
            try:
                validar_transicion(item.estado, EstadoComunicacion.cancelado)
            except TransicionInvalidaError:
                continue
            item.estado = EstadoComunicacion.cancelado
            count += 1
        await self._session.flush()
        return count

    async def listar_lote(self, lote_id: uuid.UUID) -> list[Comunicacion]:
        return list(await self._repo.list_by_lote(lote_id))
