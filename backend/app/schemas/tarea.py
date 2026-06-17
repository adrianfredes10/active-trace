"""DTOs de tareas — C-16."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.tarea import EstadoTarea


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TareaCreate(_Schema):
    asignado_a: uuid.UUID
    descripcion: str = Field(min_length=3)
    materia_id: uuid.UUID | None = None
    contexto_id: uuid.UUID | None = None


class TareaEstadoUpdate(_Schema):
    estado: EstadoTarea


class TareaDelegar(_Schema):
    asignado_a: uuid.UUID


class TareaResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID | None
    asignado_a: uuid.UUID
    asignado_por: uuid.UUID
    estado: str
    descripcion: str
    contexto_id: uuid.UUID | None


class TareaListResponse(_Schema):
    items: list[TareaResponse] = Field(default_factory=list)


class ComentarioCreate(_Schema):
    texto: str = Field(min_length=1)


class ComentarioResponse(_Schema):
    id: uuid.UUID
    tarea_id: uuid.UUID
    autor_id: uuid.UUID
    texto: str
    creado_at: datetime


class ComentarioListResponse(_Schema):
    items: list[ComentarioResponse] = Field(default_factory=list)
