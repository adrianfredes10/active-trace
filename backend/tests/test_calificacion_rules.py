"""Tests reglas de calificaciones — C-10."""

from decimal import Decimal

from app.services.calificacion_rules import (
    derivar_aprobado,
    es_columna_numerica,
    parse_nota_celda,
)


def test_rn01_columna_numerica_real() -> None:
    assert es_columna_numerica("TP1 (Real)") is True
    assert es_columna_numerica("Reflexion") is False


def test_derivar_aprobado_numerica_umbral_60() -> None:
    assert derivar_aprobado(nota_numerica=Decimal("75"), nota_textual=None) is True
    assert derivar_aprobado(nota_numerica=Decimal("45"), nota_textual=None) is False


def test_derivar_aprobado_textual_rn02() -> None:
    assert derivar_aprobado(nota_numerica=None, nota_textual="Satisfactorio") is True
    assert derivar_aprobado(nota_numerica=None, nota_textual="No satisfactorio") is False


def test_parse_nota_celda_numerica() -> None:
    num, txt = parse_nota_celda("80,5", numerica=True)
    assert num == Decimal("80.5")
    assert txt is None
