"""Servicio de calificaciones — C-10."""

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.asignacion import Asignacion
from app.models.calificacion import (
    UMBRAL_PCT_DEFECTO,
    VALORES_APROBATORIOS_DEFECTO,
    OrigenCalificacion,
    UmbralMateria,
)
from app.models.calificacion import Calificacion
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.calificacion_repository import (
    CalificacionRepository,
    UmbralMateriaRepository,
)
from app.services.analisis_service import (
    comisiones_permitidas,
    filtrar_comision_activa,
    filtrar_entradas_por_comision,
)
from app.services.calificacion_parser import (
    PreviewCalificaciones,
    preview_calificaciones_csv,
    preview_finalizacion_csv,
)
from app.services.calificacion_rules import derivar_aprobado, parse_nota_celda
from app.services.padron_service import PadronService

logger = logging.getLogger(__name__)


class CalificacionService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._calificaciones = CalificacionRepository(session, tenant_id)
        self._umbrales = UmbralMateriaRepository(session, tenant_id)
        self._padron = PadronService(session, tenant_id)
        self._asignaciones = AsignacionRepository(session, tenant_id)

    def preview_csv(self, content: bytes) -> PreviewCalificaciones:
        return preview_calificaciones_csv(content)

    async def _resolver_umbral(self, asignacion_id: uuid.UUID) -> tuple[int, list[str]]:
        umbral = await self._umbrales.get_by_asignacion(asignacion_id)
        if umbral is None:
            return UMBRAL_PCT_DEFECTO, list(VALORES_APROBATORIOS_DEFECTO)
        return umbral.umbral_pct, list(umbral.valores_aprobatorios or VALORES_APROBATORIOS_DEFECTO)

    async def _mapa_email_entrada(
        self,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        *,
        asignacion: Asignacion,
        user: CurrentUser,
        comision_activa: str | None = None,
    ) -> dict[str, uuid.UUID]:
        entradas = await self._padron.list_entradas_activas(materia_id, cohorte_id)
        permitidas = comisiones_permitidas(asignacion, user)
        entradas = filtrar_entradas_por_comision(entradas, permitidas)
        entradas = filtrar_comision_activa(entradas, comision_activa, permitidas)
        return {e.email.lower(): e.id for e in entradas}

    async def importar_calificaciones(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        actividades_seleccionadas: list[str],
        content: bytes,
        user: CurrentUser,
        comision_activa: str | None = None,
    ) -> list[Calificacion]:
        asignacion = await self._asignaciones.get(asignacion_id)
        if asignacion is None:
            raise ValueError("Asignación no encontrada")

        preview = preview_calificaciones_csv(content)
        act_map = {a.nombre: a for a in preview.actividades}
        for nombre in actividades_seleccionadas:
            if nombre not in act_map:
                raise ValueError(f"Actividad no encontrada en archivo: {nombre}")

        email_map = await self._mapa_email_entrada(
            materia_id, cohorte_id, asignacion=asignacion, user=user, comision_activa=comision_activa
        )
        umbral_pct, valores_aprob = await self._resolver_umbral(asignacion_id)
        ahora = datetime.now(timezone.utc)
        guardadas: list[Calificacion] = []

        for fila in preview.filas:
            entrada_id = email_map.get(fila.email.lower())
            if entrada_id is None:
                continue
            for actividad in actividades_seleccionadas:
                valor = fila.notas.get(actividad)
                if not valor:
                    continue
                tipo = act_map[actividad].tipo
                nota_num, nota_txt = parse_nota_celda(
                    valor, numerica=(tipo == "numerica")
                )
                aprobado = derivar_aprobado(
                    nota_numerica=nota_num,
                    nota_textual=nota_txt,
                    umbral_pct=umbral_pct,
                    valores_aprobatorios=valores_aprob,
                )
                existente = await self._calificaciones.get_by_clave(
                    asignacion_id, entrada_id, actividad
                )
                if existente:
                    existente.nota_numerica = nota_num
                    existente.nota_textual = nota_txt
                    existente.aprobado = aprobado
                    existente.importado_at = ahora
                    guardadas.append(existente)
                else:
                    cal = Calificacion(
                        asignacion_id=asignacion_id,
                        entrada_padron_id=entrada_id,
                        materia_id=materia_id,
                        actividad=actividad,
                        nota_numerica=nota_num,
                        nota_textual=nota_txt,
                        aprobado=aprobado,
                        origen=OrigenCalificacion.importado,
                        importado_at=ahora,
                    )
                    await self._calificaciones.add(cal)
                    guardadas.append(cal)

        await self._session.flush()
        logger.info(
            "calificaciones importadas asignacion=%s count=%s",
            asignacion_id,
            len(guardadas),
        )
        return guardadas

    async def configurar_umbral(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        umbral_pct: int,
        valores_aprobatorios: list[str],
    ) -> UmbralMateria:
        existente = await self._umbrales.get_by_asignacion(asignacion_id)
        if existente:
            existente.umbral_pct = umbral_pct
            existente.valores_aprobatorios = valores_aprobatorios
            existente.materia_id = materia_id
            await self._session.flush()
            return existente
        umbral = UmbralMateria(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            umbral_pct=umbral_pct,
            valores_aprobatorios=valores_aprobatorios,
        )
        await self._umbrales.add(umbral)
        return umbral

    async def get_umbral(self, asignacion_id: uuid.UUID) -> UmbralMateria | None:
        return await self._umbrales.get_by_asignacion(asignacion_id)

    async def detectar_entregas_sin_corregir(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        content: bytes,
        user: CurrentUser,
        comision_activa: str | None = None,
    ) -> list[dict[str, str]]:
        """F1.2: entregas completadas sin calificación textual registrada."""
        asignacion = await self._asignaciones.get(asignacion_id)
        if asignacion is None:
            raise ValueError("Asignación no encontrada")
        finalizadas = preview_finalizacion_csv(content)
        email_map = await self._mapa_email_entrada(
            materia_id, cohorte_id, asignacion=asignacion, user=user, comision_activa=comision_activa
        )
        calificaciones = await self._calificaciones.list_by_asignacion(asignacion_id)
        entradas_con_nota_textual: set[tuple[uuid.UUID, str]] = {
            (c.entrada_padron_id, c.actividad)
            for c in calificaciones
            if c.nota_textual or c.nota_numerica is not None
        }

        pendientes: list[dict[str, str]] = []
        for email, actividad, _estado in finalizadas:
            entrada_id = email_map.get(email.lower())
            if entrada_id is None:
                continue
            if (entrada_id, actividad) not in entradas_con_nota_textual:
                pendientes.append({"email": email, "actividad": actividad})
        return pendientes

    async def recalcular_aprobado_asignacion(self, asignacion_id: uuid.UUID) -> int:
        """Recalcula aprobado tras cambio de umbral."""
        umbral_pct, valores = await self._resolver_umbral(asignacion_id)
        calificaciones = await self._calificaciones.list_by_asignacion(asignacion_id)
        for cal in calificaciones:
            cal.aprobado = derivar_aprobado(
                nota_numerica=cal.nota_numerica,
                nota_textual=cal.nota_textual,
                umbral_pct=umbral_pct,
                valores_aprobatorios=valores,
            )
        await self._session.flush()
        return len(calificaciones)
