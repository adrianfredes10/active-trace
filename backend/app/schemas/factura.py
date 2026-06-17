"""DTOs de facturas (C-18)."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FacturaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario_id: UUID
    periodo: str = Field(pattern=r"^\d{4}-\d{2}$")
    detalle: str = Field(min_length=1)
    referencia_archivo: str | None = None
    tamano_kb: Decimal | None = Field(default=None, ge=0)


class FacturaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    usuario_id: UUID
    periodo: str
    detalle: str
    referencia_archivo: str | None
    tamano_kb: str | None
    estado: str
    cargada_at: datetime
    abonada_at: datetime | None


class FacturaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FacturaResponse]
