"""Servicio de coloquios — C-14."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
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
from app.repositories.evaluacion_repository import (
    ConvocadoEvaluacionRepository,
    EvaluacionRepository,
    ReservaEvaluacionRepository,
    ResultadoEvaluacionRepository,
    TurnoEvaluacionRepository,
)
from app.services.evaluacion_rules import (
    cupos_libres,
    puede_reservar_turno,
    validar_import_convocados,
)


@dataclass
class TurnoInput:
    fecha: date
    hora: time
    cupo_max: int


@dataclass
class ConvocatoriaMetricas:
    evaluacion_id: uuid.UUID
    materia_id: uuid.UUID
    cohorte_id: uuid.UUID
    instancia: str
    tipo: str
    estado: str
    convocados: int
    reservas_activas: int
    cupos_libres: int
    notas_registradas: int


@dataclass
class MetricasGlobales:
    convocados_total: int
    instancias_activas: int
    reservas_activas: int
    notas_registradas: int


class ColoquioService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._evaluaciones = EvaluacionRepository(session, tenant_id)
        self._turnos = TurnoEvaluacionRepository(session, tenant_id)
        self._convocados = ConvocadoEvaluacionRepository(session, tenant_id)
        self._reservas = ReservaEvaluacionRepository(session, tenant_id)
        self._resultados = ResultadoEvaluacionRepository(session, tenant_id)

    async def crear_convocatoria(
        self,
        *,
        materia_id: uuid.UUID,
        cohorte_id: uuid.UUID,
        instancia: str,
        tipo: TipoEvaluacion,
        dias_disponibles: int,
        turnos: list[TurnoInput],
    ) -> tuple[Evaluacion, list[TurnoEvaluacion]]:
        if not turnos:
            raise ValueError("Debe definir al menos un turno con cupo")
        evaluacion = Evaluacion(
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            instancia=instancia,
            tipo=tipo,
            dias_disponibles=dias_disponibles,
            estado=EstadoEvaluacion.abierta,
        )
        evaluacion = await self._evaluaciones.add(evaluacion)
        creados: list[TurnoEvaluacion] = []
        for turno in turnos:
            if turno.cupo_max < 1:
                raise ValueError("El cupo del turno debe ser al menos 1")
            creados.append(
                await self._turnos.add(
                    TurnoEvaluacion(
                        evaluacion_id=evaluacion.id,
                        fecha=turno.fecha,
                        hora=turno.hora,
                        cupo_max=turno.cupo_max,
                    )
                )
            )
        return evaluacion, creados

    async def importar_convocados(
        self, evaluacion_id: uuid.UUID, alumno_ids: list[uuid.UUID]
    ) -> int:
        evaluacion = await self._evaluaciones.get(evaluacion_id)
        if evaluacion is None:
            raise ValueError("Convocatoria no encontrada")
        ids_str = [str(a) for a in alumno_ids]
        validar_import_convocados(ids_str)
        count = 0
        for alumno_id in alumno_ids:
            if await self._convocados.is_convocado(evaluacion_id, alumno_id):
                continue
            await self._convocados.add(
                ConvocadoEvaluacion(evaluacion_id=evaluacion_id, alumno_id=alumno_id)
            )
            count += 1
        return count

    async def _cupos_libres_evaluacion(self, evaluacion_id: uuid.UUID) -> int:
        turnos = await self._turnos.list_by_evaluacion(evaluacion_id)
        total = 0
        for turno in turnos:
            activas = await self._reservas.count_activas_por_turno(turno.id)
            total += cupos_libres(cupo_max=turno.cupo_max, reservas_activas=activas)
        return total

    async def metricas_convocatoria(
        self, evaluacion_id: uuid.UUID
    ) -> ConvocatoriaMetricas:
        evaluacion = await self._evaluaciones.get(evaluacion_id)
        if evaluacion is None:
            raise ValueError("Convocatoria no encontrada")
        return ConvocatoriaMetricas(
            evaluacion_id=evaluacion.id,
            materia_id=evaluacion.materia_id,
            cohorte_id=evaluacion.cohorte_id,
            instancia=evaluacion.instancia,
            tipo=evaluacion.tipo.value,
            estado=evaluacion.estado.value,
            convocados=await self._convocados.count_by_evaluacion(evaluacion_id),
            reservas_activas=await self._reservas.count_activas_por_evaluacion(
                evaluacion_id
            ),
            cupos_libres=await self._cupos_libres_evaluacion(evaluacion_id),
            notas_registradas=await self._resultados.count_by_evaluacion(evaluacion_id),
        )

    async def listar_convocatorias(self) -> list[ConvocatoriaMetricas]:
        evaluaciones = await self._evaluaciones.list_abiertas()
        return [await self.metricas_convocatoria(e.id) for e in evaluaciones]

    async def metricas_globales(self) -> MetricasGlobales:
        evaluaciones = await self._evaluaciones.list_abiertas()
        convocados = 0
        reservas = 0
        notas = 0
        for ev in evaluaciones:
            convocados += await self._convocados.count_by_evaluacion(ev.id)
            reservas += await self._reservas.count_activas_por_evaluacion(ev.id)
            notas += await self._resultados.count_by_evaluacion(ev.id)
        return MetricasGlobales(
            convocados_total=convocados,
            instancias_activas=len(evaluaciones),
            reservas_activas=reservas,
            notas_registradas=notas,
        )

    async def reservar_turno(
        self,
        *,
        user: CurrentUser,
        evaluacion_id: uuid.UUID,
        turno_id: uuid.UUID,
    ) -> ReservaEvaluacion:
        evaluacion = await self._evaluaciones.get(evaluacion_id)
        if evaluacion is None:
            raise ValueError("Convocatoria no encontrada")
        if evaluacion.estado != EstadoEvaluacion.abierta:
            raise ValueError("La convocatoria no está abierta")
        turno = await self._turnos.get(turno_id)
        if turno is None or turno.evaluacion_id != evaluacion_id:
            raise ValueError("Turno no válido para esta convocatoria")

        es_convocado = await self._convocados.is_convocado(evaluacion_id, user.id)
        activas_turno = await self._reservas.count_activas_por_turno(turno_id)
        tiene_reserva = await self._reservas.tiene_reserva_activa(evaluacion_id, user.id)
        ok, motivo = puede_reservar_turno(
            es_convocado=es_convocado,
            cupo_disponible=cupos_libres(
                cupo_max=turno.cupo_max, reservas_activas=activas_turno
            ),
            tiene_reserva_activa=tiene_reserva,
        )
        if not ok:
            raise ValueError(motivo)

        fecha_hora = datetime.combine(turno.fecha, turno.hora, tzinfo=timezone.utc)
        return await self._reservas.add(
            ReservaEvaluacion(
                evaluacion_id=evaluacion_id,
                turno_id=turno_id,
                alumno_id=user.id,
                fecha_hora=fecha_hora,
                estado=EstadoReservaEvaluacion.activa,
            )
        )

    async def cancelar_reserva(
        self, reserva_id: uuid.UUID, user: CurrentUser
    ) -> ReservaEvaluacion:
        reserva = await self._reservas.get(reserva_id)
        if reserva is None:
            raise ValueError("Reserva no encontrada")
        if reserva.alumno_id != user.id and "COORDINADOR" not in user.roles and "ADMIN" not in user.roles:
            raise PermissionError("No puede cancelar esta reserva")
        if reserva.estado == EstadoReservaEvaluacion.cancelada:
            raise ValueError("La reserva ya está cancelada")
        reserva.estado = EstadoReservaEvaluacion.cancelada
        await self._session.flush()
        return reserva

    async def registrar_resultado(
        self,
        evaluacion_id: uuid.UUID,
        *,
        alumno_id: uuid.UUID,
        nota_final: str,
    ) -> ResultadoEvaluacion:
        evaluacion = await self._evaluaciones.get(evaluacion_id)
        if evaluacion is None:
            raise ValueError("Convocatoria no encontrada")
        if not await self._convocados.is_convocado(evaluacion_id, alumno_id):
            raise ValueError("El alumno no está convocado")
        existentes = await self._resultados.list(evaluacion_id=evaluacion_id, alumno_id=alumno_id)
        if existentes:
            resultado = existentes[0]
            resultado.nota_final = nota_final
            await self._session.flush()
            return resultado
        return await self._resultados.add(
            ResultadoEvaluacion(
                evaluacion_id=evaluacion_id,
                alumno_id=alumno_id,
                nota_final=nota_final,
            )
        )

    async def cerrar_convocatoria(self, evaluacion_id: uuid.UUID) -> Evaluacion:
        evaluacion = await self._evaluaciones.get(evaluacion_id)
        if evaluacion is None:
            raise ValueError("Convocatoria no encontrada")
        evaluacion.estado = EstadoEvaluacion.cerrada
        await self._session.flush()
        return evaluacion

    async def agenda_activa(self) -> list[ReservaEvaluacion]:
        return list(await self._reservas.list_activas())

    async def listar_resultados(self) -> list[ResultadoEvaluacion]:
        return list(await self._resultados.list_all())

    async def obtener_turnos(self, evaluacion_id: uuid.UUID) -> list[TurnoEvaluacion]:
        evaluacion = await self._evaluaciones.get(evaluacion_id)
        if evaluacion is None:
            raise ValueError("Convocatoria no encontrada")
        return list(await self._turnos.list_by_evaluacion(evaluacion_id))
