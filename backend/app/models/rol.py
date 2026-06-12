"""Catálogo de roles por tenant (C-04)."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class Rol(Base, TenantScopedMixin):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "codigo", name="uq_roles_tenant_codigo"),
    )

    codigo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        return f"<Rol codigo={self.codigo}>"
