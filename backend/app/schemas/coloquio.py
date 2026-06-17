"""DTOs de coloquios — C-14."""

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.models.evaluacion import TipoEvaluacion


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TurnoCreate(_Schema):
    fecha: date
    hora: time
    cupo_max: int = Field(ge=1, le=500)


class ConvocatoriaCreate(_Schema):
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    instancia: str = Field(min_length=2, max_length=200)
    tipo: TipoEvaluacion = TipoEvaluacion.coloquio
    dias_disponibles: int = Field(ge=0, le=365, default=0)
    turnos: list[TurnoCreate] = Field(min_length=1)


class ConvocadosImport(_Schema):
    alumno_ids: list[uuid.UUID] = Field(min_length=1)


class TurnoResponse(_Schema):
    id: uuid.UUID
    fecha: date
    hora: time
    cupo_max: int
    cupos_libres: int
    reservas_activas: int


class ConvocatoriaResponse(_Schema):
    id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    instancia: str
    tipo: str
    estado: str
    dias_disponibles: int
    turnos: list[TurnoResponse] = Field(default_factory=list)


class ConvocatoriaMetricasResponse(_Schema):
    evaluacion_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    instancia: str
    tipo: str
    estado: str
    convocados: int
    reservas_activas: int
    cupos_libres: int
    notas_registradas: int


class ConvocatoriaListResponse(_Schema):
    items: list[ConvocatoriaMetricasResponse] = Field(default_factory=list)


class MetricasGlobalesResponse(_Schema):
    convocados_total: int
    instancias_activas: int
    reservas_activas: int
    notas_registradas: int


class ReservaCreate(_Schema):
    turno_id: uuid.UUID


class ReservaResponse(_Schema):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    turno_id: uuid.UUID
    alumno_id: uuid.UUID
    fecha_hora: datetime
    estado: str


class ReservaListResponse(_Schema):
    items: list[ReservaResponse] = Field(default_factory=list)


class ResultadoCreate(_Schema):
    alumno_id: uuid.UUID
    nota_final: str = Field(min_length=1, max_length=50)


class ResultadoResponse(_Schema):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    alumno_id: uuid.UUID
    nota_final: str


class ResultadoListResponse(_Schema):
    items: list[ResultadoResponse] = Field(default_factory=list)
