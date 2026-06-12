"""DTOs de estructura académica (C-06)."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.estructura import EntidadEstado


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CarreraCreate(_Schema):
    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=255)
    estado: EntidadEstado = EntidadEstado.ACTIVA


class CarreraUpdate(_Schema):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    estado: EntidadEstado | None = None


class CarreraResponse(_Schema):
    id: uuid.UUID
    codigo: str
    nombre: str
    estado: EntidadEstado
    created_at: datetime
    updated_at: datetime


class CarreraListResponse(_Schema):
    items: list[CarreraResponse] = Field(default_factory=list)


class CohorteCreate(_Schema):
    carrera_id: uuid.UUID
    nombre: str = Field(min_length=1, max_length=100)
    anio: int = Field(ge=1900, le=2100)
    vig_desde: date
    vig_hasta: date | None = None
    estado: EntidadEstado = EntidadEstado.ACTIVA


class CohorteUpdate(_Schema):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    anio: int | None = Field(default=None, ge=1900, le=2100)
    vig_desde: date | None = None
    vig_hasta: date | None = None
    estado: EntidadEstado | None = None


class CohorteResponse(_Schema):
    id: uuid.UUID
    carrera_id: uuid.UUID
    nombre: str
    anio: int
    vig_desde: date
    vig_hasta: date | None
    estado: EntidadEstado
    created_at: datetime
    updated_at: datetime


class CohorteListResponse(_Schema):
    items: list[CohorteResponse] = Field(default_factory=list)


class MateriaCreate(_Schema):
    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=255)
    estado: EntidadEstado = EntidadEstado.ACTIVA


class MateriaUpdate(_Schema):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    estado: EntidadEstado | None = None


class MateriaResponse(_Schema):
    id: uuid.UUID
    codigo: str
    nombre: str
    estado: EntidadEstado
    created_at: datetime
    updated_at: datetime


class MateriaListResponse(_Schema):
    items: list[MateriaResponse] = Field(default_factory=list)
