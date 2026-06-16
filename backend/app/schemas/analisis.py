"""DTOs de análisis académico — C-11."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalisisContextoRequest(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID


class AlumnoAtrasadoResponse(_Schema):
    entrada_padron_id: uuid.UUID
    email: str
    nombre: str
    apellidos: str
    comision: str | None
    motivos: list[str] = Field(default_factory=list)


class AtrasadosResponse(_Schema):
    total_alumnos: int
    total_atrasados: int
    items: list[AlumnoAtrasadoResponse] = Field(default_factory=list)


class RankingItemResponse(_Schema):
    entrada_padron_id: uuid.UUID
    email: str
    nombre: str
    apellidos: str
    aprobadas: int


class RankingResponse(_Schema):
    items: list[RankingItemResponse] = Field(default_factory=list)


class ReporteRapidoResponse(_Schema):
    total_alumnos: int
    total_atrasados: int
    total_actividades: int
    tasa_aprobacion_pct: Decimal | None


class AgrupacionNotaFinal(_Schema):
    nombre: str = Field(min_length=1, max_length=100)
    actividades: list[str] = Field(min_length=1)


class AgrupacionesUpdate(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    agrupaciones: list[AgrupacionNotaFinal] = Field(default_factory=list)


class NotaFinalAlumnoResponse(_Schema):
    entrada_padron_id: uuid.UUID
    email: str
    nombre: str
    apellidos: str
    grupos: dict[str, Decimal | None] = Field(default_factory=dict)


class NotasFinalesResponse(_Schema):
    agrupaciones: list[AgrupacionNotaFinal] = Field(default_factory=list)
    items: list[NotaFinalAlumnoResponse] = Field(default_factory=list)


class SinCorregirItemResponse(_Schema):
    email: str
    nombre: str
    apellidos: str
    actividad: str


class SinCorregirResponse(_Schema):
    items: list[SinCorregirItemResponse] = Field(default_factory=list)


class MonitorFiltros(_Schema):
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    asignacion_id: uuid.UUID | None = None
    comision: str | None = None
    regional: str | None = None
    email: str | None = None
    actividad: str | None = None
    min_aprobadas: int | None = Field(default=None, ge=0)
    solo_atrasados: bool = False
    importado_desde: datetime | None = None
    importado_hasta: datetime | None = None


class MonitorAlumnoResponse(_Schema):
    entrada_padron_id: uuid.UUID
    email: str
    nombre: str
    apellidos: str
    comision: str | None
    regional: str | None
    aprobadas: int
    total_actividades: int
    atrasado: bool


class MonitorResponse(_Schema):
    items: list[MonitorAlumnoResponse] = Field(default_factory=list)
