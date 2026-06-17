"""Repository de mensajería interna — C-20."""

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy import func, or_, select

from app.models.mensaje_interno import HiloMensaje, MensajeInterno
from app.repositories.base import BaseRepository


def _ordenar_participantes(
    usuario_a: uuid.UUID, usuario_b: uuid.UUID
) -> tuple[uuid.UUID, uuid.UUID]:
    return (usuario_a, usuario_b) if usuario_a < usuario_b else (usuario_b, usuario_a)


class HiloMensajeRepository(BaseRepository[HiloMensaje]):
    model = HiloMensaje

    async def list_for_usuario(self, usuario_id: uuid.UUID) -> Sequence[HiloMensaje]:
        result = await self.session.execute(
            self._base_query()
            .where(
                or_(
                    HiloMensaje.participante_a_id == usuario_id,
                    HiloMensaje.participante_b_id == usuario_id,
                )
            )
            .order_by(HiloMensaje.ultimo_mensaje_at.desc().nullslast())
        )
        return result.scalars().all()

    async def get_for_participant(
        self, hilo_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> HiloMensaje | None:
        result = await self.session.execute(
            self._base_query().where(
                HiloMensaje.id == hilo_id,
                or_(
                    HiloMensaje.participante_a_id == usuario_id,
                    HiloMensaje.participante_b_id == usuario_id,
                ),
            )
        )
        return result.scalar_one_or_none()

    async def create_hilo(
        self,
        *,
        asunto: str,
        participante_a_id: uuid.UUID,
        participante_b_id: uuid.UUID,
        iniciado_por_id: uuid.UUID,
        ultimo_mensaje_at: datetime,
    ) -> HiloMensaje:
        a_id, b_id = _ordenar_participantes(participante_a_id, participante_b_id)
        hilo = HiloMensaje(
            asunto=asunto,
            participante_a_id=a_id,
            participante_b_id=b_id,
            iniciado_por_id=iniciado_por_id,
            ultimo_mensaje_at=ultimo_mensaje_at,
        )
        return await self.add(hilo)


class MensajeInternoRepository(BaseRepository[MensajeInterno]):
    model = MensajeInterno

    async def list_by_hilo(self, hilo_id: uuid.UUID) -> Sequence[MensajeInterno]:
        result = await self.session.execute(
            self._base_query()
            .where(MensajeInterno.hilo_id == hilo_id)
            .order_by(MensajeInterno.enviado_at.asc())
        )
        return result.scalars().all()

    async def count_by_hilo(self, hilo_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(MensajeInterno)
            .where(
                MensajeInterno.tenant_id == self.tenant_id,
                MensajeInterno.deleted_at.is_(None),
                MensajeInterno.hilo_id == hilo_id,
            )
        )
        return int(result.scalar_one())

    async def add_mensaje(
        self,
        *,
        hilo_id: uuid.UUID,
        autor_id: uuid.UUID,
        cuerpo: str,
        enviado_at: datetime | None = None,
    ) -> MensajeInterno:
        mensaje = MensajeInterno(
            hilo_id=hilo_id,
            autor_id=autor_id,
            cuerpo=cuerpo,
            enviado_at=enviado_at or datetime.now(timezone.utc),
        )
        return await self.add(mensaje)
