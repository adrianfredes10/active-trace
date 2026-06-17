"""DTOs de liquidaciones (C-18)."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SalarioBaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rol: str
    monto: Decimal = Field(gt=0)
    vig_desde: date


class SalarioBaseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    rol: str
    monto: str
    vig_desde: date
    vig_hasta: date | None


class SalarioPlusCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grupo: str = Field(min_length=1, max_length=50)
    rol: str
    monto: Decimal = Field(gt=0)
    vig_desde: date
    descripcion: str | None = None


class LiquidacionItemResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    periodo: str
    segmento: str
    usuario_id: UUID
    total: str
    estado: str
    es_nexo: bool
    excluido_por_factura: bool


class LiquidacionListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[LiquidacionItemResponse]


class LiquidacionKpisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_general: str
    total_nexo: str
    total_factura: str
    cantidad_abiertas: int


class GrillaListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[SalarioBaseResponse]
