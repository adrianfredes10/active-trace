"""Modelos de tareas internas — C-16 (E12)."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class EstadoTarea(str, enum.Enum):
    pendiente = "Pendiente"
    en_progreso = "En progreso"
    resuelta = "Resuelta"
    cancelada = "Cancelada"


class Tarea(Base, TenantScopedMixin):
    __tablename__ = "tareas"

    materia_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("materias.id"), nullable=True, index=True
    )
    asignado_a: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    asignado_por: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    estado: Mapped[EstadoTarea] = mapped_column(
        Enum(
            EstadoTarea,
            name="estado_tarea",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=EstadoTarea.pendiente,
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    contexto_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class ComentarioTarea(Base, TenantScopedMixin):
    __tablename__ = "comentarios_tarea"

    tarea_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tareas.id"), nullable=False, index=True
    )
    autor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    creado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
