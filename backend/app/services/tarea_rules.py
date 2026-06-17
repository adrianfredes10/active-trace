"""Reglas de workflow de tareas — C-16."""

from app.models.tarea import EstadoTarea

_TRANSICIONES: dict[EstadoTarea, set[EstadoTarea]] = {
    EstadoTarea.pendiente: {EstadoTarea.en_progreso, EstadoTarea.cancelada},
    EstadoTarea.en_progreso: {
        EstadoTarea.pendiente,
        EstadoTarea.resuelta,
        EstadoTarea.cancelada,
    },
    EstadoTarea.resuelta: {EstadoTarea.en_progreso},
    EstadoTarea.cancelada: set(),
}


def puede_transicionar(estado_actual: EstadoTarea, estado_nuevo: EstadoTarea) -> bool:
    if estado_actual == estado_nuevo:
        return True
    return estado_nuevo in _TRANSICIONES.get(estado_actual, set())
