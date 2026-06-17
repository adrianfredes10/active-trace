"""Repository de liquidaciones y grilla salarial (C-18)."""

import uuid
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.models.asignacion import Asignacion, RolAsignacion
from app.models.estructura import Materia
from app.models.liquidacion import (
    Liquidacion,
    LiquidacionEstado,
    ROLES_LIQUIDABLES,
    SalarioBase,
    SalarioPlus,
)
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class SalarioBaseRepository(BaseRepository[SalarioBase]):
    model = SalarioBase

    async def get_vigente(self, rol: RolAsignacion, ref: date) -> SalarioBase | None:
        result = await self.session.execute(
            self._base_query()
            .where(SalarioBase.rol == rol)
            .where(SalarioBase.vig_desde <= ref)
            .where(
                (SalarioBase.vig_hasta.is_(None)) | (SalarioBase.vig_hasta >= ref)
            )
            .order_by(SalarioBase.vig_desde.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[SalarioBase]:
        result = await self.session.execute(
            self._base_query().order_by(SalarioBase.rol, SalarioBase.vig_desde.desc())
        )
        return result.scalars().all()


class SalarioPlusRepository(BaseRepository[SalarioPlus]):
    model = SalarioPlus

    async def get_vigente(
        self, grupo: str, rol: RolAsignacion, ref: date
    ) -> SalarioPlus | None:
        result = await self.session.execute(
            self._base_query()
            .where(SalarioPlus.grupo == grupo)
            .where(SalarioPlus.rol == rol)
            .where(SalarioPlus.vig_desde <= ref)
            .where((SalarioPlus.vig_hasta.is_(None)) | (SalarioPlus.vig_hasta >= ref))
            .order_by(SalarioPlus.vig_desde.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class LiquidacionRepository(BaseRepository[Liquidacion]):
    model = Liquidacion

    async def list_periodo(
        self,
        periodo: str,
        *,
        segmento: str | None = None,
        cohorte_id: uuid.UUID | None = None,
    ) -> Sequence[Liquidacion]:
        query = self._base_query().where(Liquidacion.periodo == periodo)
        if cohorte_id is not None:
            query = query.where(Liquidacion.cohorte_id == cohorte_id)
        if segmento == "nexo":
            query = query.where(Liquidacion.es_nexo.is_(True))
        elif segmento == "factura":
            query = query.where(Liquidacion.excluido_por_factura.is_(True))
        elif segmento == "general":
            query = query.where(
                Liquidacion.es_nexo.is_(False),
                Liquidacion.excluido_por_factura.is_(False),
            )
        result = await self.session.execute(query.order_by(Liquidacion.created_at))
        return result.scalars().all()

    async def get_abierta(
        self,
        *,
        cohorte_id: uuid.UUID,
        periodo: str,
        usuario_id: uuid.UUID,
        rol: RolAsignacion,
    ) -> Liquidacion | None:
        result = await self.session.execute(
            self._base_query().where(
                Liquidacion.cohorte_id == cohorte_id,
                Liquidacion.periodo == periodo,
                Liquidacion.usuario_id == usuario_id,
                Liquidacion.rol == rol,
                Liquidacion.estado == LiquidacionEstado.abierta,
            )
        )
        return result.scalar_one_or_none()

    async def sum_totals(self, periodo: str) -> tuple[Decimal, Decimal, int]:
        """Retorna (total_general, total_nexo, cantidad_abiertas)."""
        result = await self.session.execute(
            select(
                func.coalesce(
                    func.sum(Liquidacion.total).filter(
                        Liquidacion.excluido_por_factura.is_(False)
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(Liquidacion.total).filter(Liquidacion.es_nexo.is_(True)),
                    0,
                ),
                func.count(Liquidacion.id).filter(
                    Liquidacion.estado == LiquidacionEstado.abierta
                ),
            ).where(
                Liquidacion.tenant_id == self.tenant_id,
                Liquidacion.deleted_at.is_(None),
                Liquidacion.periodo == periodo,
            )
        )
        row = result.one()
        return Decimal(str(row[0])), Decimal(str(row[1])), int(row[2])


class AsignacionLiquidacionRepository(BaseRepository[Asignacion]):
    """Consultas de asignaciones para cálculo de liquidación."""

    model = Asignacion

    async def list_liquidables_en_mes(
        self, mes_inicio: date, mes_fin: date
    ) -> Sequence[tuple[Asignacion, Materia | None, Usuario]]:
        result = await self.session.execute(
            select(Asignacion, Materia, Usuario)
            .join(Usuario, Usuario.id == Asignacion.usuario_id)
            .outerjoin(Materia, Materia.id == Asignacion.materia_id)
            .where(
                Asignacion.tenant_id == self.tenant_id,
                Asignacion.deleted_at.is_(None),
                Asignacion.rol.in_(tuple(ROLES_LIQUIDABLES)),
                Asignacion.desde <= mes_fin,
                (Asignacion.hasta.is_(None)) | (Asignacion.hasta >= mes_inicio),
                Usuario.deleted_at.is_(None),
            )
        )
        return result.all()
