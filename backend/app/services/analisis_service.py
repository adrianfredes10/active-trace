"""Servicio de análisis académico — C-11."""

import csv
import io
import logging
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.models.asignacion import Asignacion
from app.models.calificacion import Calificacion
from app.models.padron import EntradaPadron
from app.repositories.asignacion_repository import AsignacionRepository
from app.repositories.calificacion_repository import (
    CalificacionRepository,
    UmbralMateriaRepository,
)
from app.services.analisis_rules import (
    NotaAlumno,
    calcular_nota_grupo,
    contar_aprobadas,
    detectar_sin_corregir_textual,
    es_actividad_textual,
    evaluar_atrasado,
    ranking_aprobadas,
)
from app.services.padron_service import PadronService

logger = logging.getLogger(__name__)

_ROLES_AMPLIOS = frozenset({"COORDINADOR", "ADMIN"})


class AnalisisService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._calificaciones = CalificacionRepository(session, tenant_id)
        self._umbrales = UmbralMateriaRepository(session, tenant_id)
        self._asignaciones = AsignacionRepository(session, tenant_id)
        self._padron = PadronService(session, tenant_id)

    async def _resolver_asignacion(
        self, asignacion_id: uuid.UUID, user: CurrentUser
    ) -> Asignacion:
        asignacion = await self._asignaciones.get(asignacion_id)
        if asignacion is None:
            raise ValueError("Asignación no encontrada")
        if not _ROLES_AMPLIOS.intersection(user.roles):
            if asignacion.usuario_id != user.id:
                raise PermissionError("Sin acceso a esta asignación")
        return asignacion

    def _mapa_notas(
        self, calificaciones: list[Calificacion]
    ) -> dict[uuid.UUID, dict[str, NotaAlumno]]:
        por_entrada: dict[uuid.UUID, dict[str, NotaAlumno]] = {}
        for cal in calificaciones:
            bucket = por_entrada.setdefault(cal.entrada_padron_id, {})
            bucket[cal.actividad] = NotaAlumno(
                actividad=cal.actividad,
                nota_numerica=cal.nota_numerica,
                nota_textual=cal.nota_textual,
                aprobado=cal.aprobado,
            )
        return por_entrada

    async def _cargar_datos(
        self,
        *,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
        asignacion_id: uuid.UUID | None = None,
        importado_desde: datetime | None = None,
        importado_hasta: datetime | None = None,
    ) -> tuple[list[EntradaPadron], list[str], dict[uuid.UUID, dict[str, NotaAlumno]]]:
        if asignacion_id is not None:
            await self._resolver_asignacion(asignacion_id, user)
            calificaciones = list(
                await self._calificaciones.list_by_materia_cohorte(
                    materia_id,
                    asignacion_id=asignacion_id,
                    importado_desde=importado_desde,
                    importado_hasta=importado_hasta,
                )
            )
            actividades = await self._calificaciones.list_actividades_distintas(
                asignacion_id
            )
        else:
            if not _ROLES_AMPLIOS.intersection(user.roles):
                raise PermissionError("Requiere rol COORDINADOR o ADMIN")
            calificaciones = list(
                await self._calificaciones.list_by_materia_cohorte(
                    materia_id,
                    importado_desde=importado_desde,
                    importado_hasta=importado_hasta,
                )
            )
            actividades = sorted({c.actividad for c in calificaciones})

        entradas = await self._padron.list_entradas_activas(materia_id, cohorte_id)
        notas_map = self._mapa_notas(calificaciones)
        if asignacion_id is None and calificaciones:
            notas_map = self._fusionar_por_entrada(calificaciones)
        return entradas, actividades, notas_map

    def _fusionar_por_entrada(
        self, calificaciones: list[Calificacion]
    ) -> dict[uuid.UUID, dict[str, NotaAlumno]]:
        """Monitor general: última importación gana por (entrada, actividad)."""
        ordenadas = sorted(calificaciones, key=lambda c: c.importado_at)
        por_entrada: dict[uuid.UUID, dict[str, NotaAlumno]] = {}
        for cal in ordenadas:
            bucket = por_entrada.setdefault(cal.entrada_padron_id, {})
            bucket[cal.actividad] = NotaAlumno(
                actividad=cal.actividad,
                nota_numerica=cal.nota_numerica,
                nota_textual=cal.nota_textual,
                aprobado=cal.aprobado,
            )
        return por_entrada

    async def _cargar_contexto(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
        importado_desde: datetime | None = None,
        importado_hasta: datetime | None = None,
    ) -> tuple[list[EntradaPadron], list[str], dict[uuid.UUID, dict[str, NotaAlumno]]]:
        return await self._cargar_datos(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
            asignacion_id=asignacion_id,
            importado_desde=importado_desde,
            importado_hasta=importado_hasta,
        )

    async def listar_atrasados(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
    ) -> dict:
        entradas, actividades, notas_map = await self._cargar_contexto(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
        items = []
        for entrada in entradas:
            notas = notas_map.get(entrada.id, {})
            atrasado, motivos = evaluar_atrasado(actividades, notas)
            if atrasado:
                items.append(
                    {
                        "entrada_padron_id": entrada.id,
                        "email": entrada.email,
                        "nombre": entrada.nombre,
                        "apellidos": entrada.apellidos,
                        "comision": entrada.comision,
                        "motivos": motivos,
                    }
                )
        return {
            "total_alumnos": len(entradas),
            "total_atrasados": len(items),
            "items": items,
        }

    async def ranking(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
    ) -> list[dict]:
        entradas, _, notas_map = await self._cargar_contexto(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
        entrada_por_email = {e.email.lower(): e for e in entradas}
        pares = [
            (e.email.lower(), notas_map.get(e.id, {}))
            for e in entradas
        ]
        ordenados = ranking_aprobadas(pares)
        items = []
        for email, aprobadas in ordenados:
            entrada = entrada_por_email[email]
            items.append(
                {
                    "entrada_padron_id": entrada.id,
                    "email": entrada.email,
                    "nombre": entrada.nombre,
                    "apellidos": entrada.apellidos,
                    "aprobadas": aprobadas,
                }
            )
        return items

    async def reporte_rapido(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
    ) -> dict:
        atrasados = await self.listar_atrasados(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
        total_cals = await self._calificaciones.count_by_asignacion(asignacion_id)
        aprobadas = 0
        for cal in await self._calificaciones.list_by_asignacion(asignacion_id):
            if cal.aprobado:
                aprobadas += 1
        tasa = None
        if total_cals > 0:
            tasa = (Decimal(aprobadas) / Decimal(total_cals) * Decimal(100)).quantize(
                Decimal("0.01")
            )
        actividades = await self._calificaciones.list_actividades_distintas(asignacion_id)
        return {
            "total_alumnos": atrasados["total_alumnos"],
            "total_atrasados": atrasados["total_atrasados"],
            "total_actividades": len(actividades),
            "tasa_aprobacion_pct": tasa,
        }

    async def configurar_agrupaciones(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        agrupaciones: list[dict],
        user: CurrentUser,
    ) -> list[dict]:
        await self._resolver_asignacion(asignacion_id, user)
        umbral = await self._umbrales.get_by_asignacion(asignacion_id)
        payload = [
            {"nombre": g["nombre"], "actividades": g["actividades"]}
            for g in agrupaciones
        ]
        if umbral is None:
            from app.models.calificacion import UmbralMateria

            umbral = UmbralMateria(
                asignacion_id=asignacion_id,
                materia_id=materia_id,
                agrupaciones_finales=payload,
            )
            await self._umbrales.add(umbral)
        else:
            umbral.agrupaciones_finales = payload
            umbral.materia_id = materia_id
            await self._session.flush()
        return payload

    async def notas_finales(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
    ) -> dict:
        await self._resolver_asignacion(asignacion_id, user)
        umbral = await self._umbrales.get_by_asignacion(asignacion_id)
        agrupaciones = list((umbral.agrupaciones_finales if umbral else []) or [])
        entradas, _, notas_map = await self._cargar_contexto(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
        items = []
        for entrada in entradas:
            notas = notas_map.get(entrada.id, {})
            grupos: dict[str, Decimal | None] = {}
            for grupo in agrupaciones:
                grupos[grupo["nombre"]] = calcular_nota_grupo(
                    grupo["actividades"], notas
                )
            items.append(
                {
                    "entrada_padron_id": entrada.id,
                    "email": entrada.email,
                    "nombre": entrada.nombre,
                    "apellidos": entrada.apellidos,
                    "grupos": grupos,
                }
            )
        return {"agrupaciones": agrupaciones, "items": items}

    async def sin_corregir(
        self,
        *,
        asignacion_id: uuid.UUID,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        user: CurrentUser,
    ) -> list[dict]:
        entradas, actividades, notas_map = await self._cargar_contexto(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
        textuales = [a for a in actividades if es_actividad_textual(a)]
        umbral = await self._umbrales.get_by_asignacion(asignacion_id)
        if umbral and umbral.agrupaciones_finales:
            for grupo in umbral.agrupaciones_finales:
                for actividad in grupo.get("actividades", []):
                    if es_actividad_textual(actividad) and actividad not in textuales:
                        textuales.append(actividad)
        items: list[dict] = []
        for entrada in entradas:
            notas = notas_map.get(entrada.id, {})
            for actividad in detectar_sin_corregir_textual(textuales, notas):
                items.append(
                    {
                        "email": entrada.email,
                        "nombre": entrada.nombre,
                        "apellidos": entrada.apellidos,
                        "actividad": actividad,
                    }
                )
        return items

    def exportar_sin_corregir_csv(self, items: list[dict]) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["email", "nombre", "apellidos", "actividad"])
        for row in items:
            writer.writerow(
                [row["email"], row["nombre"], row["apellidos"], row["actividad"]]
            )
        return buffer.getvalue().encode("utf-8-sig")

    async def monitor(
        self,
        *,
        filtros: dict,
        user: CurrentUser,
        requiere_asignacion_propia: bool,
    ) -> list[dict]:
        asignacion_id = filtros.get("asignacion_id")
        if requiere_asignacion_propia and asignacion_id is None:
            raise ValueError("asignacion_id requerido")

        entradas, actividades, notas_map = await self._cargar_datos(
            materia_id=filtros["materia_id"],
            cohorte_id=filtros["cohorte_id"],
            user=user,
            asignacion_id=asignacion_id,
            importado_desde=filtros.get("importado_desde"),
            importado_hasta=filtros.get("importado_hasta"),
        )

        items: list[dict] = []
        for entrada in entradas:
            if filtros.get("comision") and entrada.comision != filtros["comision"]:
                continue
            if filtros.get("regional") and entrada.regional != filtros["regional"]:
                continue
            email_q = filtros.get("email")
            if email_q and email_q.lower() not in entrada.email.lower():
                continue
            notas = notas_map.get(entrada.id, {})
            if filtros.get("actividad"):
                act = filtros["actividad"]
                nota = notas.get(act)
                if nota is None or not nota.aprobado:
                    if filtros.get("min_aprobadas") is not None:
                        continue
            aprobadas = contar_aprobadas(notas)
            if filtros.get("min_aprobadas") is not None and aprobadas < filtros["min_aprobadas"]:
                continue
            atrasado, _ = evaluar_atrasado(actividades, notas)
            if filtros.get("solo_atrasados") and not atrasado:
                continue
            items.append(
                {
                    "entrada_padron_id": entrada.id,
                    "email": entrada.email,
                    "nombre": entrada.nombre,
                    "apellidos": entrada.apellidos,
                    "comision": entrada.comision,
                    "regional": entrada.regional,
                    "aprobadas": aprobadas,
                    "total_actividades": len(actividades),
                    "atrasado": atrasado,
                }
            )
        return items
