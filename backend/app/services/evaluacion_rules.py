"""Reglas de coloquios y evaluaciones — C-14."""


def cupos_libres(*, cupo_max: int, reservas_activas: int) -> int:
    return max(0, cupo_max - reservas_activas)


def puede_reservar_turno(
    *,
    es_convocado: bool,
    cupo_disponible: int,
    tiene_reserva_activa: bool,
) -> tuple[bool, str]:
    if not es_convocado:
        return False, "El alumno no está convocado a esta evaluación"
    if tiene_reserva_activa:
        return False, "El alumno ya tiene una reserva activa"
    if cupo_disponible <= 0:
        return False, "No hay cupo disponible en el turno seleccionado"
    return True, ""


def validar_import_convocados(alumno_ids: list[str]) -> None:
    if len(alumno_ids) != len(set(alumno_ids)):
        raise ValueError("Lista de convocados con IDs duplicados")
