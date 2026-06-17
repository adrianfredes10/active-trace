"""Modelos de encuentros y guardias — C-13 (E9, E10, E11)."""

import enum
import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class DiaSemana(str, enum.Enum):
    lunes = "Lunes"
    martes = "Martes"
    miercoles = "Miércoles"
    jueves = "Jueves"
    viernes = "Viernes"
    sabado = "Sábado"
    domingo = "Domingo"


class EstadoInstanciaEncuentro(str, enum.Enum):
    programado = "Programado"
    realizado = "Realizado"
    cancelado = "Cancelado"


class EstadoGuardia(str, enum.Enum):
    pendiente = "Pendiente"
    realizada = "Realizada"
    cancelada = "Cancelada"


class SlotEncuentro(Base, TenantScopedMixin):
    __tablename__ = "slots_encuentro"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asignaciones.id"), nullable=False, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    dia_semana: Mapped[DiaSemana | None] = mapped_column(
        Enum(DiaSemana, name="dia_semana"), nullable=True
    )
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    cant_semanas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fecha_unica: Mapped[date | None] = mapped_column(Date, nullable=True)
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)


class InstanciaEncuentro(Base, TenantScopedMixin):
    __tablename__ = "instancias_encuentro"

    slot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("slots_encuentro.id"), nullable=True, index=True
    )
    materia_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    hora: Mapped[time] = mapped_column(Time, nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    estado: Mapped[EstadoInstanciaEncuentro] = mapped_column(
        Enum(EstadoInstanciaEncuentro, name="estado_instancia_encuentro"),
        nullable=False,
        default=EstadoInstanciaEncuentro.programado,
    )
    meet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)


class Guardia(Base, TenantScopedMixin):
    __tablename__ = "guardias"

    asignacion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("asignaciones.id"), nullable=False, index=True
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
    dia: Mapped[DiaSemana] = mapped_column(
        Enum(DiaSemana, name="dia_semana", create_constraint=False),
        nullable=False,
    )
    horario: Mapped[str] = mapped_column(String(50), nullable=False)
    estado: Mapped[EstadoGuardia] = mapped_column(
        Enum(EstadoGuardia, name="estado_guardia"),
        nullable=False,
        default=EstadoGuardia.pendiente,
    )
    comentarios: Mapped[str | None] = mapped_column(Text, nullable=True)
    creada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
