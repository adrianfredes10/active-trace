"""DTOs de bandeja de mensajes internos — C-20."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MensajeCreate(_Schema):
    destinatario_id: uuid.UUID
    asunto: str = Field(min_length=1, max_length=200)
    cuerpo: str = Field(min_length=1, max_length=10000)


class MensajeResponder(_Schema):
    cuerpo: str = Field(min_length=1, max_length=10000)


class HiloResumen(_Schema):
    id: uuid.UUID
    asunto: str
    otro_participante_id: uuid.UUID
    ultimo_mensaje_at: datetime | None
    mensajes_count: int


class HiloListResponse(_Schema):
    items: list[HiloResumen] = Field(default_factory=list)


class MensajeResponse(_Schema):
    id: uuid.UUID
    autor_id: uuid.UUID
    cuerpo: str
    enviado_at: datetime


class HiloDetalleResponse(_Schema):
    id: uuid.UUID
    asunto: str
    participante_a_id: uuid.UUID
    participante_b_id: uuid.UUID
    mensajes: list[MensajeResponse] = Field(default_factory=list)


class MensajeCreadoResponse(_Schema):
    hilo_id: uuid.UUID
    mensaje_id: uuid.UUID
