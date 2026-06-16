"""DTOs de equipos docentes — C-08."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.asignacion import RolAsignacion
from app.schemas.asignacion import AsignacionResponse


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EquipoContexto(_Schema):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID


class AsignacionMasivaRequest(_Schema):
    usuario_ids: list[uuid.UUID] = Field(min_length=1)
    rol: RolAsignacion
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    comisiones: list[str] = Field(default_factory=list)
    desde: date
    hasta: date | None = None


class ClonarEquipoRequest(_Schema):
    origen: EquipoContexto
    destino: EquipoContexto
    desde: date
    hasta: date | None = None


class ModificarVigenciaEquipoRequest(_Schema):
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    desde: date
    hasta: date | None = None


class EquipoListResponse(_Schema):
    items: list[AsignacionResponse] = Field(default_factory=list)


class OperacionEquipoResponse(_Schema):
    creadas: int = 0
    actualizadas: int = 0
    items: list[AsignacionResponse] = Field(default_factory=list)
