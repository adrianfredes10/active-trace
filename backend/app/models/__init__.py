"""Modelos de dominio. Importados aquí para que Alembic los detecte."""

from app.models.asignacion import Asignacion, RolAsignacion
from app.models.audit_log import AuditLog
from app.models.auth_token import PasswordResetToken, RefreshToken
from app.models.base import TenantScopedMixin, TimestampSoftDeleteMixin
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.models.calificacion import Calificacion, OrigenCalificacion, UmbralMateria
from app.models.padron import EntradaPadron, VersionPadron
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant, TenantEstado
from app.models.usuario import Usuario, UsuarioEstado
from app.models.usuario_rol import UsuarioRol

__all__ = [
    "Asignacion",
    "RolAsignacion",
    "AuditLog",
    "Carrera",
    "Cohorte",
    "EntidadEstado",
    "Materia",
    "PasswordResetToken",
    "Calificacion",
    "OrigenCalificacion",
    "UmbralMateria",
    "EntradaPadron",
    "VersionPadron",
    "Permiso",
    "RefreshToken",
    "Rol",
    "RolPermiso",
    "Tenant",
    "TenantEstado",
    "TenantScopedMixin",
    "TimestampSoftDeleteMixin",
    "Usuario",
    "UsuarioEstado",
    "UsuarioRol",
]
