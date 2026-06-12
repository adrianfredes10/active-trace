"""DTOs del audit log (C-05)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AuditLogItem(_Schema):
    id: uuid.UUID
    fecha_hora: datetime
    actor_id: uuid.UUID
    impersonado_id: uuid.UUID | None = None
    materia_id: uuid.UUID | None = None
    accion: str
    detalle: dict | None = None
    filas_afectadas: int
    ip: str | None = None


class AuditLogListResponse(_Schema):
    items: list[AuditLogItem] = Field(default_factory=list)
