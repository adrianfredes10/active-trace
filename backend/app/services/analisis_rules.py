"""Reglas puras de análisis académico — C-11 (RN-06, RN-09)."""

from dataclasses import dataclass
from decimal import Decimal

from app.services.calificacion_rules import es_columna_numerica


@dataclass(frozen=True)
class NotaAlumno:
    actividad: str
    nota_numerica: Decimal | None
    nota_textual: str | None
    aprobado: bool


def es_actividad_textual(actividad: str) -> bool:
    return not es_columna_numerica(actividad)


def evaluar_atrasado(
    actividades: list[str],
    notas: dict[str, NotaAlumno],
) -> tuple[bool, list[str]]:
    """RN-06: faltante o no aprobada."""
    motivos: list[str] = []
    for actividad in actividades:
        nota = notas.get(actividad)
        if nota is None:
            motivos.append(f"{actividad}: faltante")
        elif not nota.aprobado:
            motivos.append(f"{actividad}: no aprobada")
    return len(motivos) > 0, motivos


def contar_aprobadas(notas: dict[str, NotaAlumno]) -> int:
    return sum(1 for n in notas.values() if n.aprobado)


def ranking_aprobadas(
    alumnos: list[tuple[str, dict[str, NotaAlumno]]],
) -> list[tuple[str, int]]:
    """RN-09: solo alumnos con ≥1 aprobada, orden desc."""
    filtrados = [
        (email, contar_aprobadas(notas))
        for email, notas in alumnos
        if contar_aprobadas(notas) >= 1
    ]
    return sorted(filtrados, key=lambda x: x[1], reverse=True)


def calcular_nota_grupo(
    actividades: list[str],
    notas: dict[str, NotaAlumno],
) -> Decimal | None:
    """Promedio de notas numéricas del grupo."""
    valores: list[Decimal] = []
    for actividad in actividades:
        nota = notas.get(actividad)
        if nota and nota.nota_numerica is not None:
            valores.append(nota.nota_numerica)
    if not valores:
        return None
    return sum(valores) / Decimal(len(valores))


def detectar_sin_corregir_textual(
    actividades_textuales: list[str],
    notas: dict[str, NotaAlumno],
) -> list[str]:
    """RN-08: solo actividades textuales sin calificación registrada."""
    pendientes: list[str] = []
    for actividad in actividades_textuales:
        nota = notas.get(actividad)
        if nota is None:
            pendientes.append(actividad)
        elif nota.nota_textual is None and nota.nota_numerica is None:
            pendientes.append(actividad)
    return pendientes
