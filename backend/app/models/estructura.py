"""Entidades de estructura académica (C-06): Carrera, Cohorte, Materia."""

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class EntidadEstado(str, enum.Enum):
    ACTIVA = "Activa"
    INACTIVA = "Inactiva"


class Carrera(Base, TenantScopedMixin):
    __tablename__ = "carreras"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_carreras_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EntidadEstado] = mapped_column(
        Enum(
            EntidadEstado,
            name="entidad_estado",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=EntidadEstado.ACTIVA,
        nullable=False,
    )


class Cohorte(Base, TenantScopedMixin):
    __tablename__ = "cohortes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "carrera_id",
            "nombre",
            name="uq_cohortes_tenant_carrera_nombre",
        ),
    )

    carrera_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carreras.id"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    anio: Mapped[int] = mapped_column(Integer, nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EntidadEstado] = mapped_column(
        Enum(
            EntidadEstado,
            name="entidad_estado",
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=EntidadEstado.ACTIVA,
        nullable=False,
    )


class Materia(Base, TenantScopedMixin):
    __tablename__ = "materias"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_materias_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    plus_grupo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estado: Mapped[EntidadEstado] = mapped_column(
        Enum(
            EntidadEstado,
            name="entidad_estado",
            create_constraint=False,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=EntidadEstado.ACTIVA,
        nullable=False,
    )
