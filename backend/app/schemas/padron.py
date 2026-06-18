"""DTOs de padrón — C-09."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FilaPadronPreview(_Schema):
    nombre: str
    apellidos: str
    email: str
    comision: str | None = None
    regional: str | None = None


class PadronPreviewResponse(_Schema):
    total: int
    filas: list[FilaPadronPreview] = Field(default_factory=list)


class EntradaPadronResponse(_Schema):
    id: uuid.UUID
    nombre: str
    apellidos: str
    comision: str | None
    regional: str | None
    usuario_id: uuid.UUID | None


class VersionPadronResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    cargado_por: uuid.UUID
    cargado_at: datetime
    activa: bool
    total_entradas: int = 0


class PadronImportResponse(_Schema):
    version: VersionPadronResponse
    entradas: list[EntradaPadronResponse] = Field(default_factory=list)


class MoodleSyncRequest(_Schema):
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    moodle_course_id: int = Field(gt=0)


class VaciarPadronResponse(_Schema):
    versiones_eliminadas: int


class ActualizarComisionRequest(_Schema):
    comision: str = Field(min_length=1, max_length=100)
