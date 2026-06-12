"""Link mínimo usuario↔rol a nivel tenant (C-04).

C-07 agrega `Asignacion` con contexto académico y vigencia encima de esto.
"""

import uuid

from sqlalchemy import ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class UsuarioRol(Base, TenantScopedMixin):
    __tablename__ = "usuarios_roles"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "usuario_id", "rol_id", name="uq_usuarios_roles_tenant_pair"
        ),
    )

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    rol_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id"), nullable=False, index=True
    )
