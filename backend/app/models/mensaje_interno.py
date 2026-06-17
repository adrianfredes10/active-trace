"""Mensajería interna entre usuarios del sistema — C-20 (FL-10)."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class HiloMensaje(Base, TenantScopedMixin):
    """Conversación entre dos usuarios del tenant."""

    __tablename__ = "hilos_mensaje"

    asunto: Mapped[str] = mapped_column(String(200), nullable=False)
    participante_a_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    participante_b_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    iniciado_por_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=False
    )
    ultimo_mensaje_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class MensajeInterno(Base, TenantScopedMixin):
    """Mensaje individual dentro de un hilo."""

    __tablename__ = "mensajes_internos"

    hilo_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hilos_mensaje.id"), nullable=False, index=True
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    enviado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
