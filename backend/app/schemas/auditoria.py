"""DTOs del panel de auditoría — C-19."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.audit import AuditLogItem


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AccionPorDiaItem(_Schema):
    dia: date
    accion: str
    total: int


class AccionesPorDiaResponse(_Schema):
    items: list[AccionPorDiaItem] = Field(default_factory=list)


class ComunicacionEstadoItem(_Schema):
    enviado_por: uuid.UUID
    estado: str
    total: int


class ComunicacionesPorDocenteResponse(_Schema):
    items: list[ComunicacionEstadoItem] = Field(default_factory=list)


class InteraccionItem(_Schema):
    actor_id: uuid.UUID
    materia_id: uuid.UUID | None
    accion: str
    total: int


class InteraccionesResponse(_Schema):
    items: list[InteraccionItem] = Field(default_factory=list)


class AuditoriaLogResponse(_Schema):
    items: list[AuditLogItem] = Field(default_factory=list)
    limit: int
