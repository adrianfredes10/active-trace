"""E-AUD — Log de auditoría append-only (C-05).

Inmutable: sin soft delete, sin updated_at. UPDATE/DELETE bloqueados por trigger DB.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False, index=True
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=False, index=True
    )
    impersonado_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("usuarios.id"), nullable=True, index=True
    )
    materia_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    accion: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    detalle: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    filas_afectadas: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog accion={self.accion} actor={self.actor_id}>"
