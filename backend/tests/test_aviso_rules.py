"""Tests reglas de avisos — C-15."""

import uuid
from datetime import datetime, timezone

from app.services.aviso_rules import (
    aplica_a_usuario,
    debe_mostrar_aviso,
    en_vigencia,
)

MID = uuid.uuid4()
COH = uuid.uuid4()
T0 = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)


def test_en_vigencia_respeta_ventana() -> None:
    assert en_vigencia(inicio_en=T0, fin_en=T2, ahora=T1) is True
    assert en_vigencia(inicio_en=T0, fin_en=T2, ahora=T0) is True
    assert en_vigencia(inicio_en=T0, fin_en=None, ahora=T2) is True
    assert en_vigencia(inicio_en=T0, fin_en=T2, ahora=T0.replace(day=1, hour=11)) is False
    assert en_vigencia(inicio_en=T0, fin_en=T2, ahora=T2.replace(hour=13)) is False


def test_aplica_a_usuario_por_alcance() -> None:
    roles = ["ALUMNO"]
    assert aplica_a_usuario(
        alcance="Global",
        materia_id=None,
        cohorte_id=None,
        rol_destino=None,
        user_roles=roles,
        user_materia_ids=set(),
        user_cohorte_ids=set(),
    )
    assert aplica_a_usuario(
        alcance="PorMateria",
        materia_id=MID,
        cohorte_id=None,
        rol_destino=None,
        user_roles=roles,
        user_materia_ids={MID},
        user_cohorte_ids=set(),
    )
    assert not aplica_a_usuario(
        alcance="PorCohorte",
        materia_id=None,
        cohorte_id=COH,
        rol_destino=None,
        user_roles=roles,
        user_materia_ids=set(),
        user_cohorte_ids=set(),
    )
    assert aplica_a_usuario(
        alcance="PorRol",
        materia_id=None,
        cohorte_id=None,
        rol_destino="ALUMNO",
        user_roles=roles,
        user_materia_ids=set(),
        user_cohorte_ids=set(),
    )


def test_debe_mostrar_aviso_con_ack() -> None:
    assert debe_mostrar_aviso(requiere_ack=True, ya_confirmo=False) is True
    assert debe_mostrar_aviso(requiere_ack=True, ya_confirmo=True) is False
    assert debe_mostrar_aviso(requiere_ack=False, ya_confirmo=True) is True
