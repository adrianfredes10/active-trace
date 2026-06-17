"""Generación HTML para aula virtual — C-17 (F5.4)."""

import html
from datetime import date

from app.models.programa_academico import FechaAcademica


def generar_html_fechas(fechas: list[FechaAcademica], *, materia_nombre: str) -> str:
    filas = []
    for f in sorted(fechas, key=lambda x: (x.fecha, x.numero)):
        filas.append(
            "<tr>"
            f"<td>{html.escape(f.tipo.value)}</td>"
            f"<td>{f.numero}</td>"
            f"<td>{html.escape(f.titulo)}</td>"
            f"<td>{html.escape(f.fecha.isoformat())}</td>"
            f"<td>{html.escape(f.periodo)}</td>"
            "</tr>"
        )
    body = "".join(filas) or "<tr><td colspan='5'>Sin fechas registradas</td></tr>"
    return (
        f"<h3>Cronograma de evaluaciones — {html.escape(materia_nombre)}</h3>"
        "<table border='1' cellpadding='4'>"
        "<thead><tr><th>Tipo</th><th>Nº</th><th>Título</th><th>Fecha</th><th>Período</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )
