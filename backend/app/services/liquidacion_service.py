"""Servicio de liquidaciones (C-18) — cálculo RN-21/33/34/35/37."""

from __future__ import annotations

import calendar
import uuid
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asignacion import Asignacion, RolAsignacion
from app.models.estructura import Materia
from app.models.liquidacion import (
    Liquidacion,
    LiquidacionEstado,
    SalarioBase,
    SalarioPlus,
)
from app.models.usuario import Usuario
from app.repositories.factura_repository import FacturaRepository
from app.repositories.liquidacion_repository import (
    AsignacionLiquidacionRepository,
    LiquidacionRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)


class LiquidacionCerradaError(ValueError):
    pass


class LiquidacionNoEncontradaError(ValueError):
    pass


def _periodo_bounds(periodo: str) -> tuple[date, date]:
    year, month = (int(p) for p in periodo.split("-", 1))
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _segmento_item(liq: Liquidacion) -> str:
    if liq.excluido_por_factura:
        return "factura"
    if liq.es_nexo:
        return "nexo"
    return "general"


def _contar_plus_por_grupo(
    filas: list[tuple[Asignacion, Materia | None, Usuario]],
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for asignacion, materia, _usuario in filas:
        grupo = materia.plus_grupo if materia and materia.plus_grupo else None
        if not grupo:
            continue
        comisiones = asignacion.comisiones or []
        counts[grupo] += max(len(comisiones), 1)
    return counts


class LiquidacionService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.liq_repo = LiquidacionRepository(session, tenant_id)
        self.base_repo = SalarioBaseRepository(session, tenant_id)
        self.plus_repo = SalarioPlusRepository(session, tenant_id)
        self.asig_repo = AsignacionLiquidacionRepository(session, tenant_id)
        self.factura_repo = FacturaRepository(session, tenant_id)

    async def calcular_periodo(self, periodo: str) -> list[Liquidacion]:
        mes_inicio, mes_fin = _periodo_bounds(periodo)
        ref = mes_inicio
        filas = await self.asig_repo.list_liquidables_en_mes(mes_inicio, mes_fin)

        grupos: dict[tuple[uuid.UUID, uuid.UUID, RolAsignacion], list] = defaultdict(
            list
        )
        for asignacion, materia, usuario in filas:
            if asignacion.cohorte_id is None:
                continue
            key = (asignacion.usuario_id, asignacion.cohorte_id, asignacion.rol)
            grupos[key].append((asignacion, materia, usuario))

        creadas: list[Liquidacion] = []
        for (usuario_id, cohorte_id, rol), items in grupos.items():
            usuario = items[0][2]
            existente = await self.liq_repo.get_abierta(
                cohorte_id=cohorte_id,
                periodo=periodo,
                usuario_id=usuario_id,
                rol=rol,
            )
            if existente is not None:
                continue

            comisiones_labels: list[str] = []
            for asignacion, _materia, _u in items:
                for c in asignacion.comisiones or []:
                    comisiones_labels.append(str(c))

            es_nexo = rol == RolAsignacion.nexo
            excluido = bool(usuario.facturador)

            if excluido:
                monto_base = Decimal("0")
                monto_plus = Decimal("0")
            else:
                base = await self.base_repo.get_vigente(rol, ref)
                monto_base = base.monto if base else Decimal("0")
                plus_counts = _contar_plus_por_grupo(items)
                monto_plus = Decimal("0")
                for grupo, n in plus_counts.items():
                    plus = await self.plus_repo.get_vigente(grupo, rol, ref)
                    if plus:
                        monto_plus += plus.monto * n

            total = monto_base + monto_plus
            liq = await self.liq_repo.add(
                Liquidacion(
                    cohorte_id=cohorte_id,
                    periodo=periodo,
                    usuario_id=usuario_id,
                    rol=rol,
                    comisiones=comisiones_labels,
                    monto_base=monto_base,
                    monto_plus=monto_plus,
                    total=total,
                    es_nexo=es_nexo,
                    excluido_por_factura=excluido,
                    estado=LiquidacionEstado.abierta,
                )
            )
            creadas.append(liq)

        await self.session.flush()
        return creadas

    async def listar(
        self, periodo: str, segmento: str = "general"
    ) -> list[Liquidacion]:
        existentes = await self.liq_repo.list_periodo(periodo)
        if not existentes:
            await self.calcular_periodo(periodo)
        return list(await self.liq_repo.list_periodo(periodo, segmento=segmento))

    async def kpis(self, periodo: str) -> dict[str, str | int]:
        existentes = await self.liq_repo.list_periodo(periodo)
        if not existentes:
            await self.calcular_periodo(periodo)
        total_general, total_nexo, abiertas = await self.liq_repo.sum_totals(periodo)
        factura_count = await self.factura_repo.sum_periodo(periodo)
        return {
            "total_general": _decimal_str(total_general),
            "total_nexo": _decimal_str(total_nexo),
            "total_factura": _decimal_str(factura_count),
            "cantidad_abiertas": abiertas,
        }

    async def cerrar(self, liquidacion_id: uuid.UUID) -> Liquidacion:
        liq = await self.liq_repo.get(liquidacion_id)
        if liq is None:
            raise LiquidacionNoEncontradaError("Liquidación no encontrada")
        if liq.estado == LiquidacionEstado.cerrada:
            raise LiquidacionCerradaError("La liquidación ya está cerrada")
        liq.estado = LiquidacionEstado.cerrada
        await self.session.flush()
        return liq

    async def listar_grilla(self) -> list[SalarioBase]:
        return list(await self.base_repo.list_all())

    async def crear_salario_base(
        self, rol: str, monto: Decimal, vig_desde: date
    ) -> SalarioBase:
        try:
            rol_enum = RolAsignacion(rol)
        except ValueError as exc:
            raise ValueError(f"Rol inválido: {rol}") from exc
        return await self.base_repo.add(
            SalarioBase(rol=rol_enum, monto=monto, vig_desde=vig_desde)
        )

    async def crear_salario_plus(
        self,
        grupo: str,
        rol: str,
        monto: Decimal,
        vig_desde: date,
        descripcion: str | None = None,
    ) -> SalarioPlus:
        try:
            rol_enum = RolAsignacion(rol)
        except ValueError as exc:
            raise ValueError(f"Rol inválido: {rol}") from exc
        return await self.plus_repo.add(
            SalarioPlus(
                grupo=grupo,
                rol=rol_enum,
                monto=monto,
                vig_desde=vig_desde,
                descripcion=descripcion,
            )
        )

    @staticmethod
    def to_item_response(liq: Liquidacion) -> dict:
        return {
            "id": liq.id,
            "periodo": liq.periodo,
            "segmento": _segmento_item(liq),
            "usuario_id": liq.usuario_id,
            "total": _decimal_str(liq.total),
            "estado": liq.estado.value,
            "es_nexo": liq.es_nexo,
            "excluido_por_factura": liq.excluido_por_factura,
        }
