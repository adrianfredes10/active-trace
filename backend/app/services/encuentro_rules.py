"""Reglas de generación de instancias — C-13 (RN-13)."""

from datetime import date, timedelta

from app.models.encuentro import DiaSemana

_DIA_A_WEEKDAY = {
    DiaSemana.lunes: 0,
    DiaSemana.martes: 1,
    DiaSemana.miercoles: 2,
    DiaSemana.jueves: 3,
    DiaSemana.viernes: 4,
    DiaSemana.sabado: 5,
    DiaSemana.domingo: 6,
}


def _primer_dia(fecha_inicio: date, dia_semana: DiaSemana) -> date:
    objetivo = _DIA_A_WEEKDAY[dia_semana]
    delta = (objetivo - fecha_inicio.weekday()) % 7
    return fecha_inicio + timedelta(days=delta)


def generar_fechas_recurrente(
    fecha_inicio: date, dia_semana: DiaSemana, cant_semanas: int
) -> list[date]:
    if cant_semanas < 1:
        raise ValueError("cant_semanas debe ser >= 1 para modo recurrente")
    primera = _primer_dia(fecha_inicio, dia_semana)
    return [primera + timedelta(weeks=i) for i in range(cant_semanas)]
