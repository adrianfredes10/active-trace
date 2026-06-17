"""Reglas de avisos — C-15 (RN-18, RN-19, RN-20)."""

import uuid
from datetime import datetime


def en_vigencia(
    *,
    inicio_en: datetime,
    fin_en: datetime | None,
    ahora: datetime,
) -> bool:
    if ahora < inicio_en:
        return False
    if fin_en is not None and ahora > fin_en:
        return False
    return True


def aplica_a_usuario(
    *,
    alcance: str,
    materia_id: uuid.UUID | None,
    cohorte_id: uuid.UUID | None,
    rol_destino: str | None,
    user_roles: list[str],
    user_materia_ids: set[uuid.UUID],
    user_cohorte_ids: set[uuid.UUID],
) -> bool:
    if rol_destino is not None and rol_destino not in user_roles:
        return False
    if alcance == "Global":
        return True
    if alcance == "PorMateria":
        return materia_id is not None and materia_id in user_materia_ids
    if alcance == "PorCohorte":
        return cohorte_id is not None and cohorte_id in user_cohorte_ids
    if alcance == "PorRol":
        return rol_destino is not None and rol_destino in user_roles
    return False


def debe_mostrar_aviso(*, requiere_ack: bool, ya_confirmo: bool) -> bool:
    if requiere_ack and ya_confirmo:
        return False
    return True
