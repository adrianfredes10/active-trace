"""Matriz rol × permiso por tenant (C-04)."""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class RolPermiso(Base, TenantScopedMixin):
    __tablename__ = "roles_permisos"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "rol_id", "permiso_id", name="uq_roles_permisos_tenant_pair"
        ),
    )

    rol_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id"), nullable=False, index=True
    )
    permiso_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("permisos.id"), nullable=False, index=True
    )
