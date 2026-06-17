"""Reglas de estado de comunicaciones — C-12 (RN-15, RN-17)."""

from app.models.comunicacion import EstadoComunicacion

_TRANSICIONES: dict[EstadoComunicacion, set[EstadoComunicacion]] = {
    EstadoComunicacion.pendiente: {
        EstadoComunicacion.enviando,
        EstadoComunicacion.cancelado,
    },
    EstadoComunicacion.enviando: {
        EstadoComunicacion.enviado,
        EstadoComunicacion.error,
    },
    EstadoComunicacion.enviado: set(),
    EstadoComunicacion.error: set(),
    EstadoComunicacion.cancelado: set(),
}


class TransicionInvalidaError(ValueError):
    pass


def puede_transicionar(
    actual: EstadoComunicacion, nuevo: EstadoComunicacion
) -> bool:
    return nuevo in _TRANSICIONES.get(actual, set())


def validar_transicion(
    actual: EstadoComunicacion, nuevo: EstadoComunicacion
) -> None:
    if not puede_transicionar(actual, nuevo):
        raise TransicionInvalidaError(
            f"Transición inválida: {actual.value} → {nuevo.value}"
        )


def listo_para_despacho(*, aprobado: bool, es_masivo: bool, requiere_aprobacion: bool) -> bool:
    """RN-17: masivo sin aprobación queda en cola."""
    if es_masivo and requiere_aprobacion and not aprobado:
        return False
    return True


def requiere_aprobacion_masiva(cantidad_destinatarios: int) -> bool:
    return cantidad_destinatarios > 1
