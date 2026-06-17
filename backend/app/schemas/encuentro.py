"""DTOs de encuentros — C-13."""

import uuid
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.encuentro import DiaSemana, EstadoInstanciaEncuentro


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SlotRecurrenteCreate(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    titulo: str = Field(min_length=1, max_length=200)
    hora: time
    dia_semana: DiaSemana
    fecha_inicio: date
    cant_semanas: int = Field(ge=1, le=52)
    meet_url: str | None = Field(default=None, max_length=500)
    vig_desde: date
    vig_hasta: date | None = None


class EncuentroUnicoCreate(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    titulo: str = Field(min_length=1, max_length=200)
    fecha: date
    hora: time
    meet_url: str | None = Field(default=None, max_length=500)


class InstanciaEncuentroUpdate(_Schema):
    estado: EstadoInstanciaEncuentro | None = None
    meet_url: str | None = Field(default=None, max_length=500)
    video_url: str | None = Field(default=None, max_length=500)
    comentario: str | None = None


class InstanciaEncuentroResponse(_Schema):
    id: uuid.UUID
    slot_id: uuid.UUID | None
    materia_id: uuid.UUID
    fecha: date
    hora: time
    titulo: str
    estado: str
    meet_url: str | None
    video_url: str | None
    comentario: str | None


class InstanciaListResponse(_Schema):
    items: list[InstanciaEncuentroResponse] = Field(default_factory=list)


class SlotEncuentroResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID
    titulo: str
    instancias_generadas: int


class HtmlEncuentrosResponse(_Schema):
    html: str
