"""Modelos de calificaciones y umbral — C-10 (E7, E8)."""

import enum
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin

UMBRAL_PCT_DEFECTO = 60
VALORES_APROBATORIOS_DEFECTO = ["Satisfactorio", "Supera lo esperado"]


class OrigenCalificacion(str, enum.Enum):
    importado = "Importado"
    manual = "Manual"


class Calificacion(Base, TenantScopedMixin):
    __tablename__ = "calificaciones"

    asignacion_id: Mapped[UUID] = mapped_column(
        ForeignKey("asignaciones.id"), nullable=False, index=True
    )
    entrada_padron_id: Mapped[UUID] = mapped_column(
        ForeignKey("entradas_padron.id"), nullable=False, index=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    actividad: Mapped[str] = mapped_column(String(255), nullable=False)
    nota_numerica: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    nota_textual: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aprobado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origen: Mapped[OrigenCalificacion] = mapped_column(
        Enum(OrigenCalificacion, name="origen_calificacion"),
        nullable=False,
        default=OrigenCalificacion.importado,
    )
    importado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UmbralMateria(Base, TenantScopedMixin):
    __tablename__ = "umbrales_materia"

    asignacion_id: Mapped[UUID] = mapped_column(
        ForeignKey("asignaciones.id"), nullable=False, unique=True
    )
    materia_id: Mapped[UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    umbral_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=UMBRAL_PCT_DEFECTO)
    valores_aprobatorios: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=lambda: list(VALORES_APROBATORIOS_DEFECTO)
    )
    agrupaciones_finales: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list
    )
