"""Entidad `Tenant`: raíz del modelo multi-tenant.

NO hereda `TenantScopedMixin` (no lleva `tenant_id`): es la raíz del
aislamiento, no un sujeto de él.
"""

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampSoftDeleteMixin


class TenantEstado(str, enum.Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"


class Tenant(Base, TimestampSoftDeleteMixin):
    __tablename__ = "tenants"

    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    estado: Mapped[TenantEstado] = mapped_column(
        Enum(TenantEstado, name="tenant_estado"),
        default=TenantEstado.ACTIVO,
        nullable=False,
    )
    aprobacion_masiva_comunicaciones: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Tenant id={self.id} slug={self.slug!r}>"
