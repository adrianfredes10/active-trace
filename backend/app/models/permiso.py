"""Permisos finos `modulo:accion` por tenant (C-04)."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class Permiso(Base, TenantScopedMixin):
    __tablename__ = "permisos"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "modulo", "accion", name="uq_permisos_tenant_modulo_accion"
        ),
    )

    modulo: Mapped[str] = mapped_column(String(50), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)

    @property
    def clave(self) -> str:
        return f"{self.modulo}:{self.accion}"

    def __repr__(self) -> str:
        return f"<Permiso {self.modulo}:{self.accion}>"
