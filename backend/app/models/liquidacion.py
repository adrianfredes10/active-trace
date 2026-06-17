"""Modelos de liquidaciones y honorarios (C-18): grilla, liquidación, factura."""

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.asignacion import RolAsignacion, rol_asignacion_column
from app.models.base import TenantScopedMixin


class LiquidacionEstado(str, enum.Enum):
    abierta = "Abierta"
    cerrada = "Cerrada"


class FacturaEstado(str, enum.Enum):
    pendiente = "Pendiente"
    abonada = "Abonada"


ROLES_LIQUIDABLES = frozenset(
    {
        RolAsignacion.profesor,
        RolAsignacion.tutor,
        RolAsignacion.coordinador,
        RolAsignacion.nexo,
    }
)


class SalarioBase(Base, TenantScopedMixin):
    __tablename__ = "salarios_base"

    rol: Mapped[RolAsignacion] = mapped_column(
        rol_asignacion_column(create_constraint=False),
        nullable=False,
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)


class SalarioPlus(Base, TenantScopedMixin):
    __tablename__ = "salarios_plus"

    grupo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    rol: Mapped[RolAsignacion] = mapped_column(
        rol_asignacion_column(create_constraint=False),
        nullable=False,
    )
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    vig_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vig_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)


class Liquidacion(Base, TenantScopedMixin):
    __tablename__ = "liquidaciones"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "cohorte_id",
            "periodo",
            "usuario_id",
            "rol",
            name="uq_liquidaciones_tenant_cohorte_periodo_usuario_rol",
        ),
    )

    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohortes.id"), nullable=False, index=True
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    rol: Mapped[RolAsignacion] = mapped_column(
        rol_asignacion_column(create_constraint=False),
        nullable=False,
    )
    comisiones: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    monto_base: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monto_plus: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    es_nexo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    excluido_por_factura: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    estado: Mapped[LiquidacionEstado] = mapped_column(
        Enum(
            LiquidacionEstado,
            name="liquidacion_estado",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=LiquidacionEstado.abierta,
        nullable=False,
    )


class Factura(Base, TenantScopedMixin):
    __tablename__ = "facturas"

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    detalle: Mapped[str] = mapped_column(Text, nullable=False)
    referencia_archivo: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tamano_kb: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estado: Mapped[FacturaEstado] = mapped_column(
        Enum(FacturaEstado, name="factura_estado"),
        default=FacturaEstado.pendiente,
        nullable=False,
    )
    cargada_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    abonada_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
