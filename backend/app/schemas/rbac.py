"""DTOs RBAC (C-04)."""

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RolCatalogItem(_Schema):
    codigo: str
    nombre: str
    permisos: list[str] = Field(default_factory=list)


class CatalogoResponse(_Schema):
    roles: list[RolCatalogItem]


class PermisosEfectivosResponse(_Schema):
    permisos: list[str]


class MessageResponse(_Schema):
    detail: str
