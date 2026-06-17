"""Tests reglas de comunicaciones — C-12."""

import pytest

from app.models.comunicacion import EstadoComunicacion
from app.services.comunicacion_rules import (
    TransicionInvalidaError,
    listo_para_despacho,
    puede_transicionar,
    requiere_aprobacion_masiva,
    validar_transicion,
)


def test_rn15_transiciones_validas() -> None:
    assert puede_transicionar(
        EstadoComunicacion.pendiente, EstadoComunicacion.enviando
    )
    assert puede_transicionar(
        EstadoComunicacion.enviando, EstadoComunicacion.enviado
    )


def test_rn15_transicion_invalida() -> None:
    with pytest.raises(TransicionInvalidaError):
        validar_transicion(EstadoComunicacion.enviado, EstadoComunicacion.pendiente)


def test_rn17_masivo_requiere_aprobacion() -> None:
    assert requiere_aprobacion_masiva(2) is True
    assert requiere_aprobacion_masiva(1) is False
    assert listo_para_despacho(
        aprobado=False, es_masivo=True, requiere_aprobacion=True
    ) is False
    assert listo_para_despacho(
        aprobado=True, es_masivo=True, requiere_aprobacion=True
    ) is True
