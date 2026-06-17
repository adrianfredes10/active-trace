"""Entidad `Asignacion` — C-07.

Vincula un Usuario con un Rol dentro de un contexto académico concreto
(materia / carrera / cohorte) con vigencia temporal (desde / hasta).

Es el eje del modelo de autorización: una asignación vencida no otorga
permisos pero se conserva en el histórico (soft delete + vigencia).

La propiedad `vigente` es derivada (no se almacena) para evitar
inconsistencias: se calcula en Python sobre `desde` y `hasta`.
"""

import enum
from datetime import date
from uuid import UUID

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin


class RolAsignacion(str, enum.Enum):
    alumno = "ALUMNO"
    tutor = "TUTOR"
    profesor = "PROFESOR"
    coordinador = "COORDINADOR"
    nexo = "NEXO"
    admin = "ADMIN"
    finanzas = "FINANZAS"


def rol_asignacion_column(**kwargs: object) -> Enum:
    return Enum(
        RolAsignacion,
        name="rol_asignacion",
        values_callable=lambda enum_cls: [member.value for member in enum_cls],
        **kwargs,
    )


class Asignacion(Base, TenantScopedMixin):
    __tablename__ = "asignaciones"

    usuario_id: Mapped[UUID] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    rol: Mapped[RolAsignacion] = mapped_column(
        rol_asignacion_column(), nullable=False
    )

    materia_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("materias.id"), nullable=True, index=True
    )
    carrera_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("carreras.id"), nullable=True, index=True
    )
    cohorte_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cohortes.id"), nullable=True, index=True
    )
    comisiones: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    responsable_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )

    desde: Mapped[date] = mapped_column(Date, nullable=False)
    hasta: Mapped[date | None] = mapped_column(Date, nullable=True)

    @property
    def vigente(self) -> bool:
        hoy = date.today()
        if self.desde > hoy:
            return False
        if self.hasta is not None and self.hasta < hoy:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"<Asignacion id={self.id} "
            f"usuario={self.usuario_id} "
            f"rol={self.rol} "
            f"vigente={self.vigente}>"
        )
