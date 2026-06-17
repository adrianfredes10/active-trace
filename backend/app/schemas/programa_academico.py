"""DTOs de programas y fechas académicas — C-17."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluacion import TipoEvaluacion


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProgramaCreate(_Schema):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    titulo: str = Field(min_length=2, max_length=200)
    nombre_archivo: str = Field(min_length=1, max_length=255)


class ProgramaResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    titulo: str
    referencia_archivo: str
    cargado_at: datetime


class ProgramaListResponse(_Schema):
    items: list[ProgramaResponse] = Field(default_factory=list)


class FechaAcademicaCreate(_Schema):
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: TipoEvaluacion
    numero: int = Field(ge=1, le=99)
    periodo: str = Field(min_length=2, max_length=20)
    fecha: date
    titulo: str = Field(min_length=2, max_length=200)


class FechaAcademicaUpdate(_Schema):
    tipo: TipoEvaluacion | None = None
    numero: int | None = Field(default=None, ge=1, le=99)
    periodo: str | None = Field(default=None, min_length=2, max_length=20)
    fecha: date | None = None
    titulo: str | None = Field(default=None, min_length=2, max_length=200)


class FechaAcademicaResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    tipo: str
    numero: int
    periodo: str
    fecha: date
    titulo: str


class FechaAcademicaListResponse(_Schema):
    items: list[FechaAcademicaResponse] = Field(default_factory=list)


class HtmlFechasResponse(_Schema):
    html: str
