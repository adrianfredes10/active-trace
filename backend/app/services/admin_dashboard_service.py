"""Resumen académico agregado por tenant — panel admin."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calificacion import Calificacion
from app.models.estructura import Carrera, Cohorte, Materia
from app.models.padron import EntradaPadron, VersionPadron


class AdminDashboardService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id

    async def resumen_academico(self) -> dict:
        alumnos_q = (
            select(func.count())
            .select_from(EntradaPadron)
            .join(
                VersionPadron,
                EntradaPadron.version_id == VersionPadron.id,
            )
            .where(
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
                VersionPadron.tenant_id == self._tenant_id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            )
        )
        total_alumnos = int((await self._session.execute(alumnos_q)).scalar_one())

        comision_q = (
            select(EntradaPadron.comision, func.count())
            .join(
                VersionPadron,
                EntradaPadron.version_id == VersionPadron.id,
            )
            .where(
                EntradaPadron.tenant_id == self._tenant_id,
                EntradaPadron.deleted_at.is_(None),
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
                EntradaPadron.comision.is_not(None),
            )
            .group_by(EntradaPadron.comision)
            .order_by(EntradaPadron.comision)
        )
        por_comision = [
            {"comision": row[0] or "—", "total": int(row[1])}
            for row in (await self._session.execute(comision_q)).all()
        ]

        cal_filters = (
            Calificacion.tenant_id == self._tenant_id,
            Calificacion.deleted_at.is_(None),
        )
        total_cals = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Calificacion).where(*cal_filters)
                )
            ).scalar_one()
        )
        aprobadas = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(Calificacion)
                    .where(*cal_filters, Calificacion.aprobado.is_(True))
                )
            ).scalar_one()
        )
        pendientes = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(Calificacion)
                    .where(*cal_filters, Calificacion.aprobado.is_(False))
                )
            ).scalar_one()
        )

        total_materias = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(Materia)
                    .where(
                        Materia.tenant_id == self._tenant_id,
                        Materia.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        total_carreras = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(Carrera)
                    .where(
                        Carrera.tenant_id == self._tenant_id,
                        Carrera.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )
        total_cohortes = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(Cohorte)
                    .where(
                        Cohorte.tenant_id == self._tenant_id,
                        Cohorte.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )

        return {
            "total_alumnos": total_alumnos,
            "total_calificaciones": total_cals,
            "entregas_aprobadas": aprobadas,
            "entregas_pendientes": pendientes,
            "total_materias": total_materias,
            "total_carreras": total_carreras,
            "total_cohortes": total_cohortes,
            "por_comision": por_comision,
        }
