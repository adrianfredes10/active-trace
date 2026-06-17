"""DTOs de guardias — C-13."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.encuentro import DiaSemana, EstadoGuardia


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GuardiaCreate(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: DiaSemana
    horario: str = Field(min_length=3, max_length=50)
    comentarios: str | None = None


class GuardiaUpdate(_Schema):
    estado: EstadoGuardia | None = None
    comentarios: str | None = None


class GuardiaResponse(_Schema):
    id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    dia: str
    horario: str
    estado: str
    comentarios: str | None
    creada_at: datetime


class GuardiaListResponse(_Schema):
    items: list[GuardiaResponse] = Field(default_factory=list)
