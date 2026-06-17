"""Modelos de avisos — C-15 (E13)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class AlcanceAviso(str, enum.Enum):
    global_ = "Global"
    por_materia = "PorMateria"
    por_cohorte = "PorCohorte"
    por_rol = "PorRol"


class SeveridadAviso(str, enum.Enum):
    info = "Info"
    advertencia = "Advertencia"
    critico = "Crítico"


class Aviso(Base, TenantScopedMixin):
    __tablename__ = "avisos"

    alcance: Mapped[AlcanceAviso] = mapped_column(
        Enum(
            AlcanceAviso,
            name="alcance_aviso",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("materias.id"), nullable=True, index=True
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cohortes.id"), nullable=True, index=True
    )
    rol_destino: Mapped[str | None] = mapped_column(String(30), nullable=True)
    severidad: Mapped[SeveridadAviso] = mapped_column(
        Enum(
            SeveridadAviso,
            name="severidad_aviso",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    cuerpo: Mapped[str] = mapped_column(Text, nullable=False)
    inicio_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requiere_ack: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class AcknowledgmentAviso(Base, TenantScopedMixin):
    __tablename__ = "acknowledgments_aviso"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "aviso_id", "usuario_id", name="uq_ack_aviso_usuario"
        ),
    )

    aviso_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("avisos.id"), nullable=False, index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    confirmado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
