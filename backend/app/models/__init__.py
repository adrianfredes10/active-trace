"""Modelos de dominio. Importados aquí para que Alembic los detecte."""

from app.models.programa_academico import FechaAcademica, ProgramaMateria
from app.models.tarea import ComentarioTarea, EstadoTarea, Tarea
from app.models.aviso import AcknowledgmentAviso, AlcanceAviso, Aviso, SeveridadAviso
from app.models.asignacion import Asignacion, RolAsignacion
from app.models.audit_log import AuditLog
from app.models.auth_token import PasswordResetToken, RefreshToken
from app.models.base import TenantScopedMixin, TimestampSoftDeleteMixin
from app.models.estructura import Carrera, Cohorte, EntidadEstado, Materia
from app.models.calificacion import Calificacion, OrigenCalificacion, UmbralMateria
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.models.evaluacion import (
    ConvocadoEvaluacion,
    EstadoEvaluacion,
    EstadoReservaEvaluacion,
    Evaluacion,
    ReservaEvaluacion,
    ResultadoEvaluacion,
    TipoEvaluacion,
    TurnoEvaluacion,
)
from app.models.encuentro import (
    DiaSemana,
    EstadoGuardia,
    EstadoInstanciaEncuentro,
    Guardia,
    InstanciaEncuentro,
    SlotEncuentro,
)
from app.models.liquidacion import (
    Factura,
    FacturaEstado,
    Liquidacion,
    LiquidacionEstado,
    SalarioBase,
    SalarioPlus,
)
from app.models.mensaje_interno import HiloMensaje, MensajeInterno
from app.models.padron import EntradaPadron, VersionPadron
from app.models.permiso import Permiso
from app.models.rol import Rol
from app.models.rol_permiso import RolPermiso
from app.models.tenant import Tenant, TenantEstado
from app.models.usuario import Usuario, UsuarioEstado
from app.models.usuario_rol import UsuarioRol

__all__ = [
    "AcknowledgmentAviso",
    "AlcanceAviso",
    "Asignacion",
    "RolAsignacion",
    "AuditLog",
    "Aviso",
    "Carrera",
    "Cohorte",
    "ComentarioTarea",
    "EntidadEstado",
    "Materia",
    "Liquidacion",
    "LiquidacionEstado",
    "PasswordResetToken",
    "Calificacion",
    "Comunicacion",
    "ConvocadoEvaluacion",
    "DiaSemana",
    "EstadoEvaluacion",
    "EstadoReservaEvaluacion",
    "EstadoTarea",
    "EstadoComunicacion",
    "EstadoGuardia",
    "EstadoInstanciaEncuentro",
    "Guardia",
    "Factura",
    "FacturaEstado",
    "HiloMensaje",
    "InstanciaEncuentro",
    "SlotEncuentro",
    "MensajeInterno",
    "OrigenCalificacion",
    "SalarioBase",
    "SalarioPlus",
    "UmbralMateria",
    "EntradaPadron",
    "Evaluacion",
    "FechaAcademica",
    "VersionPadron",
    "Permiso",
    "ProgramaMateria",
    "RefreshToken",
    "ReservaEvaluacion",
    "ResultadoEvaluacion",
    "Rol",
    "RolPermiso",
    "SeveridadAviso",
    "Tenant",
    "TenantEstado",
    "Tarea",
    "TenantScopedMixin",
    "TimestampSoftDeleteMixin",
    "TipoEvaluacion",
    "TurnoEvaluacion",
    "Usuario",
    "UsuarioEstado",
    "UsuarioRol",
]
