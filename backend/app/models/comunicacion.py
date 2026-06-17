"""Modelo de cola de comunicaciones — C-12 (E21)."""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedMixin


class EstadoComunicacion(str, enum.Enum):
    pendiente = "Pendiente"
    enviando = "Enviando"
    enviado = "Enviado"
    error = "Error"
    cancelado = "Cancelado"


class Comunicacion(Base, TenantScopedMixin):
    __tablename__ = "comunicaciones"

    enviado_por: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    destinatario: Mapped[str] = mapped_column(EncryptedString(512), nullable=False)
    asunto: Mapped[str] = mapped_column(String(255), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoComunicacion] = mapped_column(
        Enum(
            EstadoComunicacion,
            name="estado_comunicacion",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=EstadoComunicacion.pendiente,
    )
    lote_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    es_masivo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    aprobado_por: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    aprobado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_detalle: Mapped[str | None] = mapped_column(String(500), nullable=True)
