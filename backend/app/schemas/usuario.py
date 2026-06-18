"""DTOs de Usuario — C-07.

UsuarioResponse NUNCA expone campos PII (dni, cuil, cbu, alias_cbu).
Si un endpoint necesita devolver PII, debe usar un schema dedicado con
autorización explícita — no el response genérico.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.usuario import UsuarioEstado


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UsuarioCreate(_Schema):
    email: EmailStr
    password: str = Field(min_length=8)
    nombre: str | None = Field(default=None, max_length=100)
    apellidos: str | None = Field(default=None, max_length=150)
    banco: str | None = Field(default=None, max_length=100)
    regional: str | None = Field(default=None, max_length=100)
    legajo: str | None = Field(default=None, max_length=50)
    legajo_profesional: str | None = Field(default=None, max_length=50)
    facturador: bool = False


class UsuarioUpdate(_Schema):
    nombre: str | None = Field(default=None, max_length=100)
    apellidos: str | None = Field(default=None, max_length=150)
    banco: str | None = Field(default=None, max_length=100)
    regional: str | None = Field(default=None, max_length=100)
    legajo: str | None = Field(default=None, max_length=50)
    legajo_profesional: str | None = Field(default=None, max_length=50)
    facturador: bool | None = None
    estado: UsuarioEstado | None = None


class UsuarioPIIUpdate(_Schema):
    """Actualización de campos PII — requiere permiso `usuarios:editar_pii`."""

    dni: str | None = Field(default=None, max_length=20)
    cuil: str | None = Field(default=None, max_length=20)
    cbu: str | None = Field(default=None, max_length=30)
    alias_cbu: str | None = Field(default=None, max_length=100)


class UsuarioResponse(_Schema):
    """Respuesta pública: PII excluida deliberadamente."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: uuid.UUID
    nombre: str | None
    apellidos: str | None
    banco: str | None
    regional: str | None
    legajo: str | None
    legajo_profesional: str | None
    facturador: bool
    estado: UsuarioEstado
    created_at: datetime
    updated_at: datetime


class UsuarioListResponse(_Schema):
    items: list[UsuarioResponse] = Field(default_factory=list)


class ProfesorAltaRequest(_Schema):
    email: EmailStr
    password: str = Field(min_length=8)
    nombre: str | None = Field(default=None, max_length=100)
    apellidos: str | None = Field(default=None, max_length=150)
    materia_id: uuid.UUID
    carrera_id: uuid.UUID
    cohorte_id: uuid.UUID
    comision: str = Field(min_length=1, max_length=100)


class ProfesorAltaResponse(_Schema):
    usuario: UsuarioResponse
    asignacion_id: uuid.UUID
    comision: str
