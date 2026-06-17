"""Tests reglas de tareas — C-16."""

import pytest

from app.models.tarea import EstadoTarea
from app.services.tarea_rules import puede_transicionar


def test_transiciones_validas() -> None:
    assert puede_transicionar(EstadoTarea.pendiente, EstadoTarea.en_progreso)
    assert puede_transicionar(EstadoTarea.en_progreso, EstadoTarea.resuelta)
    assert puede_transicionar(EstadoTarea.resuelta, EstadoTarea.en_progreso)


def test_transiciones_invalidas() -> None:
    assert not puede_transicionar(EstadoTarea.pendiente, EstadoTarea.resuelta)
    assert not puede_transicionar(EstadoTarea.cancelada, EstadoTarea.pendiente)


def test_mismo_estado_siempre_ok() -> None:
    assert puede_transicionar(EstadoTarea.pendiente, EstadoTarea.pendiente)
