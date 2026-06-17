"""Tests almacenamiento opaco y HTML fechas — C-17."""

import uuid

from app.services.fecha_academica_html import generar_html_fechas
from app.services.programa_storage import generar_referencia_archivo


def test_referencia_archivo_es_opaca() -> None:
    tid = uuid.uuid4()
    ref = generar_referencia_archivo(tid, "programa.pdf")
    assert ref.startswith(f"ref:{tid}:")
    assert "programa.pdf" in ref
    assert "/" not in ref.split(":", 3)[-1]


def test_generar_html_fechas_incluye_titulos() -> None:
    class _F:
        tipo = type("T", (), {"value": "Parcial"})()
        numero = 1
        titulo = "Primer parcial"
        fecha = __import__("datetime").date(2026, 6, 20)
        periodo = "2026-1"

    html = generar_html_fechas([_F()], materia_nombre="Prog I")
    assert "Cronograma" in html
    assert "Primer parcial" in html
