"""DTOs de perfil propio — C-20 (F11.1)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.usuario import UsuarioEstado


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PerfilUpdate(_Schema):
    """Campos editables por el usuario autenticado. CUIL excluido deliberadamente."""

    nombre: str | None = Field(default=None, max_length=100)
    apellidos: str | None = Field(default=None, max_length=150)
    dni: str | None = Field(default=None, max_length=20)
    banco: str | None = Field(default=None, max_length=100)
    cbu: str | None = Field(default=None, max_length=30)
    alias_cbu: str | None = Field(default=None, max_length=100)
    regional: str | None = Field(default=None, max_length=100)
    legajo_profesional: str | None = Field(default=None, max_length=50)
    facturador: bool | None = None


class PerfilResponse(_Schema):
    """Perfil propio: incluye PII del titular; CUIL solo lectura."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    nombre: str | None
    apellidos: str | None
    dni: str | None
    cuil: str | None
    banco: str | None
    cbu: str | None
    alias_cbu: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: UsuarioEstado
    created_at: datetime
    updated_at: datetime
