"""Modelos de evaluaciones y coloquios — C-14 (E14)."""

import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class TipoEvaluacion(str, enum.Enum):
    parcial = "Parcial"
    tp = "TP"
    coloquio = "Coloquio"
    recuperatorio = "Recuperatorio"


class EstadoEvaluacion(str, enum.Enum):
    abierta = "Abierta"
    cerrada = "Cerrada"


class EstadoReservaEvaluacion(str, enum.Enum):
    activa = "Activa"
    cancelada = "Cancelada"


class Evaluacion(Base, TenantScopedMixin):
    __tablename__ = "evaluaciones"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohortes.id"), nullable=False, index=True
    )
    tipo: Mapped[TipoEvaluacion] = mapped_column(
        Enum(TipoEvaluacion, name="tipo_evaluacion"),
        nullable=False,
        default=TipoEvaluacion.coloquio,
    )
    instancia: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[EstadoEvaluacion] = mapped_column(
        Enum(EstadoEvaluacion, name="estado_evaluacion"),
        nullable=False,
        default=EstadoEvaluacion.abierta,
    )
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class TurnoEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "turnos_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluaciones.id"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    cupo_max: Mapped[int] = mapped_column(Integer, nullable=False)


class ConvocadoEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "convocados_evaluacion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "evaluacion_id",
            "alumno_id",
            name="uq_convocado_evaluacion_alumno",
        ),
    )

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluaciones.id"), nullable=False, index=True
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )


class ReservaEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "reservas_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluaciones.id"), nullable=False, index=True
    )
    turno_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("turnos_evaluacion.id"), nullable=False, index=True
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[EstadoReservaEvaluacion] = mapped_column(
        Enum(EstadoReservaEvaluacion, name="estado_reserva_evaluacion"),
        nullable=False,
        default=EstadoReservaEvaluacion.activa,
    )


class ResultadoEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "resultados_evaluacion"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "evaluacion_id",
            "alumno_id",
            name="uq_resultado_evaluacion_alumno",
        ),
    )

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluaciones.id"), nullable=False, index=True
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    nota_final: Mapped[str] = mapped_column(String(50), nullable=False)
