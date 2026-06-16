"""Entidad `Usuario`.

Identidad base del sistema. Contiene credenciales de autenticación (C-03)
y atributos de negocio / PII cifrada (C-07: nombre, DNI, CUIL, CBU, legajo).

El `email` se guarda cifrado (AES-256) y se busca por `email_hash`
(blind index determinista), porque el cifrado GCM no es consultable.

Atributos PII cifrados: email, totp_secret, dni, cuil, cbu, alias_cbu.
Nunca deben aparecer en logs, repr ni respuestas HTTP sin tratamiento explícito.
"""

import enum

from sqlalchemy import Boolean, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedMixin


class UsuarioEstado(str, enum.Enum):
    activo = "Activo"
    inactivo = "Inactivo"


class Usuario(Base, TenantScopedMixin):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email_hash", name="uq_usuarios_tenant_email_hash"),
    )

    # --- autenticación (C-03) ---
    email: Mapped[str] = mapped_column(EncryptedString(512), nullable=False)
    email_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    two_factor_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    totp_secret: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)

    # --- negocio (C-07) ---
    nombre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    apellidos: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # PII cifrada
    dni: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)
    cuil: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)
    cbu: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)
    alias_cbu: Mapped[str | None] = mapped_column(EncryptedString(512), nullable=True)

    banco: Mapped[str | None] = mapped_column(String(100), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(100), nullable=True)
    legajo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    legajo_profesional: Mapped[str | None] = mapped_column(String(50), nullable=True)
    facturador: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estado: Mapped[UsuarioEstado] = mapped_column(
        Enum(UsuarioEstado, name="usuario_estado"),
        default=UsuarioEstado.activo,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Usuario id={self.id} estado={self.estado}>"
