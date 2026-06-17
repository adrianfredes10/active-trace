"""Reglas de negocio de coloquios — C-14."""

import pytest

from app.services.evaluacion_rules import (
    cupos_libres,
    puede_reservar_turno,
    validar_import_convocados,
)


def test_cupos_libres_resta_reservas_activas() -> None:
    assert cupos_libres(cupo_max=5, reservas_activas=3) == 2
    assert cupos_libres(cupo_max=2, reservas_activas=2) == 0


def test_puede_reservar_requiere_convocado_y_cupo() -> None:
    ok, _ = puede_reservar_turno(
        es_convocado=True, cupo_disponible=1, tiene_reserva_activa=False
    )
    assert ok is True

    ok, motivo = puede_reservar_turno(
        es_convocado=False, cupo_disponible=1, tiene_reserva_activa=False
    )
    assert ok is False
    assert "convocado" in motivo.lower()

    ok, motivo = puede_reservar_turno(
        es_convocado=True, cupo_disponible=0, tiene_reserva_activa=False
    )
    assert ok is False
    assert "cupo" in motivo.lower()

    ok, motivo = puede_reservar_turno(
        es_convocado=True, cupo_disponible=1, tiene_reserva_activa=True
    )
    assert ok is False
    assert "reserva" in motivo.lower()


def test_validar_import_convocados_rechaza_duplicados() -> None:
    with pytest.raises(ValueError, match="duplicado"):
        validar_import_convocados(["a", "a"])
