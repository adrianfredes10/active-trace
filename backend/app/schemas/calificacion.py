"""DTOs de calificaciones — C-10."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.calificacion import UMBRAL_PCT_DEFECTO, VALORES_APROBATORIOS_DEFECTO


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ActividadDetectadaResponse(_Schema):
    nombre: str
    tipo: str


class CalificacionPreviewResponse(_Schema):
    actividades: list[ActividadDetectadaResponse] = Field(default_factory=list)
    total_filas: int
    muestra_emails: list[str] = Field(default_factory=list)


class CalificacionImportRequest(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    actividades: list[str] = Field(min_length=1)


class CalificacionResponse(_Schema):
    id: uuid.UUID
    entrada_padron_id: uuid.UUID
    actividad: str
    nota_numerica: Decimal | None
    nota_textual: str | None
    aprobado: bool
    origen: str
    importado_at: datetime


class CalificacionImportResponse(_Schema):
    importadas: int
    items: list[CalificacionResponse] = Field(default_factory=list)


class UmbralMateriaUpdate(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    umbral_pct: int = Field(default=UMBRAL_PCT_DEFECTO, ge=0, le=100)
    valores_aprobatorios: list[str] = Field(
        default_factory=lambda: list(VALORES_APROBATORIOS_DEFECTO)
    )


class UmbralMateriaResponse(_Schema):
    id: uuid.UUID
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    umbral_pct: int
    valores_aprobatorios: list[str]


class FinalizacionPreviewRequest(_Schema):
    asignacion_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID


class EntregaSinCorregirResponse(_Schema):
    items: list[dict[str, str]] = Field(default_factory=list)
