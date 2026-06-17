"""Utilidades de almacenamiento opaco — C-17."""

import uuid


def generar_referencia_archivo(tenant_id: uuid.UUID, nombre_archivo: str) -> str:
    """Referencia opaca al blob; no expone rutas internas del servidor."""
    token = uuid.uuid4().hex
    safe_name = nombre_archivo.replace("/", "_").replace("\\", "_")[:120]
    return f"ref:{tenant_id}:{token}:{safe_name}"
