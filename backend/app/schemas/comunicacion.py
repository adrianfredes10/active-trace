"""Schemas de comunicaciones — C-12."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DestinatarioComunicacion(_Schema):
    email: str = Field(min_length=3, max_length=255)
    nombre: str = Field(min_length=1, max_length=100)
    apellidos: str = Field(min_length=1, max_length=150)


class ComunicacionPreviewRequest(_Schema):
    asunto: str = Field(min_length=1, max_length=255)
    cuerpo: str = Field(min_length=1)
    muestra: DestinatarioComunicacion


class ComunicacionPreviewResponse(_Schema):
    asunto: str
    cuerpo: str


class ComunicacionEnviarRequest(_Schema):
    materia_id: uuid.UUID
    asunto: str = Field(min_length=1, max_length=255)
    cuerpo: str = Field(min_length=1)
    destinatarios: list[DestinatarioComunicacion] = Field(min_length=1)
    confirmo_preview: bool


class ComunicacionResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID
    asunto: str
    estado: str
    lote_id: uuid.UUID
    es_masivo: bool
    aprobado: bool
    enviado_at: datetime | None


class ComunicacionEnviarResponse(_Schema):
    lote_id: uuid.UUID
    encoladas: int
    requiere_aprobacion: bool
    items: list[ComunicacionResponse] = Field(default_factory=list)


class LoteComunicacionResponse(_Schema):
    lote_id: uuid.UUID
    total: int
    items: list[ComunicacionResponse] = Field(default_factory=list)


class AprobarComunicacionResponse(_Schema):
    aprobadas: int


class CancelarComunicacionResponse(_Schema):
    canceladas: int
