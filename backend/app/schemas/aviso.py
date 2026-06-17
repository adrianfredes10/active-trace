"""DTOs de avisos — C-15."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.aviso import AlcanceAviso, SeveridadAviso


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AvisoCreate(_Schema):
    alcance: AlcanceAviso
    materia_id: uuid.UUID | None = None
    cohorte_id: uuid.UUID | None = None
    rol_destino: str | None = Field(default=None, max_length=30)
    severidad: SeveridadAviso = SeveridadAviso.info
    titulo: str = Field(min_length=2, max_length=200)
    cuerpo: str = Field(min_length=1)
    inicio_en: datetime
    fin_en: datetime | None = None
    orden: int = Field(default=0, ge=0, le=9999)
    requiere_ack: bool = False


class AvisoUpdate(_Schema):
    titulo: str | None = Field(default=None, min_length=2, max_length=200)
    cuerpo: str | None = None
    inicio_en: datetime | None = None
    fin_en: datetime | None = None
    orden: int | None = Field(default=None, ge=0, le=9999)
    activo: bool | None = None
    requiere_ack: bool | None = None
    severidad: SeveridadAviso | None = None


class AvisoResponse(_Schema):
    id: uuid.UUID
    alcance: str
    materia_id: uuid.UUID | None
    cohorte_id: uuid.UUID | None
    rol_destino: str | None
    severidad: str
    titulo: str
    cuerpo: str
    inicio_en: datetime
    fin_en: datetime | None
    orden: int
    activo: bool
    requiere_ack: bool


class AvisoListResponse(_Schema):
    items: list[AvisoResponse] = Field(default_factory=list)


class AvisoMetricasResponse(_Schema):
    aviso_id: uuid.UUID
    confirmaciones: int


class AckResponse(_Schema):
    aviso_id: uuid.UUID
    usuario_id: uuid.UUID
    confirmado_at: datetime
