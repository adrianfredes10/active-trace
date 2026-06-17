"""Tests plantillas de comunicación — C-12."""

from app.services.comunicacion_template import render_plantilla


def test_render_variables() -> None:
    texto = "Hola {{nombre}} {{apellidos}} ({{email}})"
    resultado = render_plantilla(
        texto,
        {
            "nombre": "Ana",
            "apellidos": "Garcia",
            "email": "ana@example.com",
        },
    )
    assert resultado == "Hola Ana Garcia (ana@example.com)"
