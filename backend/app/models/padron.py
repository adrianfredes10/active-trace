"""Modelos de padrón versionado — C-09 (E6).

VersionPadron: cada carga genera una versión; solo una activa por (materia, cohorte).
EntradaPadron: filas del padrón; email cifrado; usuario_id opcional.
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import EncryptedString
from app.models.base import TenantScopedMixin


class VersionPadron(Base, TenantScopedMixin):
    __tablename__ = "versiones_padron"

    materia_id: Mapped[UUID] = mapped_column(
        ForeignKey("materias.id"), nullable=False, index=True
    )
    cohorte_id: Mapped[UUID] = mapped_column(
        ForeignKey("cohortes.id"), nullable=False, index=True
    )
    cargado_por: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    cargado_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    activa: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EntradaPadron(Base, TenantScopedMixin):
    __tablename__ = "entradas_padron"

    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("versiones_padron.id"), nullable=False, index=True
    )
    usuario_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True, index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(EncryptedString(512), nullable=False)
    comision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    regional: Mapped[str | None] = mapped_column(String(100), nullable=True)
