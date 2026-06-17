"""Modelos de programas y fechas académicas — C-17 (E15, E16)."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin
from app.models.evaluacion import TipoEvaluacion


class ProgramaMateria(Base, TenantScopedMixin):
    __tablename__ = "programas_materia"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "materia_id",
            "carrera_id",
            "cohorte_id",
            name="uq_programa_materia_carrera_cohorte",
        ),
    )

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    carrera_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carreras.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohortes.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    referencia_archivo: Mapped[str] = mapped_column(String(500), nullable=False)
    cargado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class FechaAcademica(Base, TenantScopedMixin):
    __tablename__ = "fechas_academicas"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohortes.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoEvaluacion] = mapped_column(
        Enum(TipoEvaluacion, name="tipo_evaluacion", create_type=False),
        nullable=False,
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
