"""Entidad `Usuario` — versión MÍNIMA de auth (C-03).

Solo contiene los campos que la autenticación necesita. C-07 la EXTIENDE
(ALTER) con los atributos de negocio/PII (nombre, dni, cuil, cbu, legajo…)
y agrega `Asignacion`. No se recrea la tabla.

El `email` se guarda cifrado (AES-256) y se busca por `email_hash`
(blind index determinista), porque el cifrado GCM no es consultable.
"""

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedMixin


class Usuario(Base, TenantScopedMixin):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email_hash", name="uq_usuarios_tenant_email_hash"),
    )

    email: Mapped[str] = mapped_column(EncryptedString(512), nullable=False)
    email_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    totp_secret: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)

    def __repr__(self) -> str:
        # Nunca exponer email/secretos en repr.
        return f"<Usuario id={self.id} active={self.is_active}>"
