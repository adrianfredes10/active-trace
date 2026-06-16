"""Lógica de derivación de aprobado y detección de columnas — C-10."""

from decimal import Decimal, InvalidOperation

from app.models.calificacion import UMBRAL_PCT_DEFECTO, VALORES_APROBATORIOS_DEFECTO


def es_columna_numerica(header: str) -> bool:
    """RN-01: columnas cuyo encabezado termina en '(Real)'."""
    return header.strip().endswith("(Real)")


def es_columna_textual(header: str, columnas_fijas: set[str]) -> bool:
    """Actividad cualitativa: no es columna fija ni numérica (Real)."""
    norm = header.strip().lower()
    if norm in columnas_fijas:
        return False
    return not es_columna_numerica(header)


def derivar_aprobado(
    *,
    nota_numerica: Decimal | float | None,
    nota_textual: str | None,
    umbral_pct: int = UMBRAL_PCT_DEFECTO,
    valores_aprobatorios: list[str] | None = None,
) -> bool:
    """RN-02 / RN-03: deriva aprobado desde nota numérica o textual."""
    valores = valores_aprobatorios or VALORES_APROBATORIOS_DEFECTO
    if nota_numerica is not None:
        return float(nota_numerica) >= umbral_pct
    if nota_textual:
        return nota_textual.strip() in valores
    return False


def parse_nota_celda(valor: str, *, numerica: bool) -> tuple[Decimal | None, str | None]:
    texto = valor.strip()
    if not texto or texto in {"-", "—"}:
        return None, None
    if numerica:
        try:
            return Decimal(texto.replace(",", ".")), None
        except InvalidOperation:
            return None, texto
    return None, texto
