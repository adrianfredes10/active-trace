"""Tests reglas de encuentros — C-13."""

from datetime import date

from app.models.encuentro import DiaSemana
from app.services.encuentro_rules import generar_fechas_recurrente


def test_generar_instancias_recurrentes_rn13() -> None:
    fechas = generar_fechas_recurrente(
        date(2026, 3, 2), DiaSemana.lunes, 4
    )
    assert len(fechas) == 4
    assert fechas[0] == date(2026, 3, 2)
    assert fechas[1] == date(2026, 3, 9)
