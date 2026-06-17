"""DTOs de Asignacion — C-07."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.asignacion import Asignacion, RolAsignacion


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AsignacionCreate(_Schema):
    usuario_id: uuid.UUID
    rol: RolAsignacion
    materia_id: uuid.UUID | None = None
    carrera_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    comisiones: list[str] = Field(default_factory=list)
    responsable_id: uuid.UUID | None = None
    desde: date
    hasta: date | None = None


class AsignacionUpdate(_Schema):
    rol: RolAsignacion | None = None
    materia_id: uuid.UUID | None = None
    carrera_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    comisiones: list[str] | None = None
    responsable_id: uuid.UUID | None = None
    desde: date | None = None
    hasta: date | None = None


class AsignacionResponse(_Schema):
    id: uuid.UUID
    usuario_id: uuid.UUID
    rol: RolAsignacion
    materia_id: uuid.UUID | None
    carrera_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    comisiones: list[str]
    responsable_id: uuid.UUID | None
    desde: date
    hasta: date | None
    vigente: bool
    created_at: datetime
    materia_codigo: str | None = None
    materia_nombre: str | None = None
    cohorte_nombre: str | None = None
    carrera_codigo: str | None = None


class AsignacionListResponse(_Schema):
    items: list[AsignacionResponse] = Field(default_factory=list)


def asignacion_response(
    entity: Asignacion,
    *,
    materia_codigo: str | None = None,
    materia_nombre: str | None = None,
    cohorte_nombre: str | None = None,
    carrera_codigo: str | None = None,
) -> AsignacionResponse:
    """Serializa Asignacion incluyendo `vigente` (propiedad derivada)."""
    return AsignacionResponse(
        id=entity.id,
        usuario_id=entity.usuario_id,
        rol=entity.rol,
        materia_id=entity.materia_id,
        carrera_id=entity.carrera_id,
        cohorte_id=entity.cohorte_id,
        comisiones=entity.comisiones or [],
        responsable_id=entity.responsable_id,
        desde=entity.desde,
        hasta=entity.hasta,
        vigente=entity.vigente,
        created_at=entity.created_at,
        materia_codigo=materia_codigo,
        materia_nombre=materia_nombre,
        cohorte_nombre=cohorte_nombre,
        carrera_codigo=carrera_codigo,
    )
