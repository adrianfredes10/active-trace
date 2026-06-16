"""Tests reglas de análisis — C-11."""

from decimal import Decimal

from app.services.analisis_rules import (
    NotaAlumno,
    calcular_nota_grupo,
    contar_aprobadas,
    detectar_sin_corregir_textual,
    evaluar_atrasado,
    ranking_aprobadas,
)


def _nota(actividad: str, num: str | None, aprobado: bool, txt: str | None = None) -> NotaAlumno:
    return NotaAlumno(
        actividad=actividad,
        nota_numerica=Decimal(num) if num else None,
        nota_textual=txt,
        aprobado=aprobado,
    )


def test_rn06_atrasado_por_faltante() -> None:
    actividades = ["TP1 (Real)", "Reflexion"]
    notas = {"TP1 (Real)": _nota("TP1 (Real)", "80", True)}
    atrasado, motivos = evaluar_atrasado(actividades, notas)
    assert atrasado is True
    assert any("faltante" in m for m in motivos)


def test_rn06_atrasado_por_umbral() -> None:
    actividades = ["TP1 (Real)"]
    notas = {"TP1 (Real)": _nota("TP1 (Real)", "45", False)}
    atrasado, _ = evaluar_atrasado(actividades, notas)
    assert atrasado is True


def test_rn09_ranking_excluye_sin_aprobadas() -> None:
    alumnos = [
        ("ana@example.com", {"TP1 (Real)": _nota("TP1 (Real)", "80", True)}),
        ("pedro@example.com", {"TP1 (Real)": _nota("TP1 (Real)", "40", False)}),
    ]
    ranking = ranking_aprobadas(alumnos)
    assert len(ranking) == 1
    assert ranking[0][0] == "ana@example.com"


def test_nota_grupo_promedio() -> None:
    notas = {
        "TP1 (Real)": _nota("TP1 (Real)", "80", True),
        "TP2 (Real)": _nota("TP2 (Real)", "60", True),
    }
    assert calcular_nota_grupo(["TP1 (Real)", "TP2 (Real)"], notas) == Decimal("70")


def test_sin_corregir_solo_textual() -> None:
    notas = {"Reflexion": _nota("Reflexion", None, False, None)}
    pendientes = detectar_sin_corregir_textual(["Reflexion"], notas)
    assert pendientes == ["Reflexion"]
