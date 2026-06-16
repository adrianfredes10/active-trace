"""Parser de archivos de calificaciones Moodle — C-10."""

import csv
import io
from dataclasses import dataclass, field

from app.services.calificacion_rules import (
    es_columna_numerica,
    es_columna_textual,
    parse_nota_celda,
)
from app.services.padron_parser import PadronParseError


@dataclass(frozen=True)
class ActividadDetectada:
    nombre: str
    tipo: str  # "numerica" | "textual"


@dataclass
class FilaCalificacionPreview:
    email: str
    nombre: str
    apellidos: str
    notas: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PreviewCalificaciones:
    actividades: list[ActividadDetectada]
    filas: list[FilaCalificacionPreview]


_COLUMNAS_FIJAS = {"email", "correo", "mail", "nombre", "name", "apellidos", "apellido", "last_name"}


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _leer_csv(content: bytes) -> tuple[list[str], list[list[str]]]:
    text = content.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text))
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise PadronParseError("Archivo vacío") from exc
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    return headers, rows


def preview_calificaciones_csv(content: bytes) -> PreviewCalificaciones:
    headers, rows = _leer_csv(content)
    header_map: dict[int, str] = {}
    email_idx: int | None = None
    nombre_idx: int | None = None
    apellidos_idx: int | None = None

    for idx, raw in enumerate(headers):
        norm = _normalize_header(raw)
        if norm in ("email", "correo", "mail"):
            email_idx = idx
            header_map[idx] = "email"
        elif norm in ("nombre", "name", "first_name"):
            nombre_idx = idx
            header_map[idx] = "nombre"
        elif norm in ("apellidos", "apellido", "last_name"):
            apellidos_idx = idx
            header_map[idx] = "apellidos"

    if email_idx is None:
        raise PadronParseError("Falta columna email en el archivo")

    actividades: list[ActividadDetectada] = []
    actividad_cols: dict[int, ActividadDetectada] = {}
    for idx, raw in enumerate(headers):
        if idx in header_map:
            continue
        if es_columna_numerica(raw):
            act = ActividadDetectada(nombre=raw.strip(), tipo="numerica")
        elif es_columna_textual(raw, _COLUMNAS_FIJAS):
            act = ActividadDetectada(nombre=raw.strip(), tipo="textual")
        else:
            continue
        actividades.append(act)
        actividad_cols[idx] = act

    if not actividades:
        raise PadronParseError("No se detectaron columnas de actividades")

    filas: list[FilaCalificacionPreview] = []
    for row in rows:
        email = row[email_idx].strip() if email_idx < len(row) else ""
        if not email:
            continue
        nombre = row[nombre_idx].strip() if nombre_idx is not None and nombre_idx < len(row) else ""
        apellidos = (
            row[apellidos_idx].strip()
            if apellidos_idx is not None and apellidos_idx < len(row)
            else ""
        )
        notas: dict[str, str] = {}
        for idx, act in actividad_cols.items():
            if idx < len(row) and row[idx].strip():
                notas[act.nombre] = row[idx].strip()
        filas.append(
            FilaCalificacionPreview(
                email=email, nombre=nombre, apellidos=apellidos, notas=notas
            )
        )

    if not filas:
        raise PadronParseError("No se encontraron filas de alumnos")
    return PreviewCalificaciones(actividades=actividades, filas=filas)


def preview_finalizacion_csv(content: bytes) -> list[tuple[str, str, str]]:
    """F1.2: retorna (email, actividad, estado) para filas completadas."""
    headers, rows = _leer_csv(content)
    email_idx = next(
        (i for i, h in enumerate(headers) if _normalize_header(h) in ("email", "correo", "mail")),
        None,
    )
    actividad_idx = next(
        (i for i, h in enumerate(headers) if _normalize_header(h) in ("actividad", "activity")),
        None,
    )
    estado_idx = next(
        (i for i, h in enumerate(headers) if _normalize_header(h) in ("estado", "status", "state")),
        None,
    )
    if email_idx is None or actividad_idx is None:
        raise PadronParseError("Faltan columnas email y actividad")

    resultado: list[tuple[str, str, str]] = []
    for row in rows:
        email = row[email_idx].strip() if email_idx < len(row) else ""
        actividad = row[actividad_idx].strip() if actividad_idx < len(row) else ""
        estado = (
            row[estado_idx].strip().lower()
            if estado_idx is not None and estado_idx < len(row)
            else "completado"
        )
        if email and actividad and estado in {"completado", "complete", "submitted", "si", "sí"}:
            resultado.append((email, actividad, estado))
    return resultado
