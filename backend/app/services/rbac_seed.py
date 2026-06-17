"""Seed idempotente del catálogo RBAC por tenant (C-04).

Matriz base derivada de `knowledge-base/03_actores_y_roles.md` §3.3.
Alcance GLOBAL: el qualifier `(propio)` se difiere a C-07.
NEXO se siembra sin permisos (PA-25 abierta).
"""

import uuid

from sqlalchemy import select, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permiso, Rol, RolPermiso

DOMAIN_ROLES: dict[str, str] = {
    "ALUMNO": "Alumno",
    "TUTOR": "Tutor",
    "PROFESOR": "Profesor",
    "COORDINADOR": "Coordinador",
    "NEXO": "Nexo",
    "ADMIN": "Administrador",
    "FINANZAS": "Finanzas",
}

ROLE_PERMISSION_KEYS: dict[str, list[str]] = {
    "ALUMNO": [
        "estado_academico:ver",
        "evaluaciones:reservar",
        "avisos:confirmar",
    ],
    "TUTOR": [
        "avisos:confirmar",
        "atrasados:ver",
        "entregas:detectar_sin_corregir",
        "encuentros:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "inbox:leer",
        "inbox:responder",
    ],
    "PROFESOR": [
        "avisos:confirmar",
        "calificaciones:importar",
        "padron:importar",
        "padron:vaciar",
        "atrasados:ver",
        "entregas:detectar_sin_corregir",
        "comunicacion:enviar",
        "encuentros:gestionar",
        "evaluaciones:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "inbox:leer",
        "inbox:responder",
    ],
    "COORDINADOR": [
        "avisos:confirmar",
        "calificaciones:importar",
        "padron:importar",
        "padron:vaciar",
        "atrasados:ver",
        "entregas:detectar_sin_corregir",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "evaluaciones:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "auditoria:ver",
        "inbox:leer",
        "inbox:responder",
    ],
    "NEXO": [],
    "ADMIN": [
        "avisos:confirmar",
        "calificaciones:importar",
        "atrasados:ver",
        "entregas:detectar_sin_corregir",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentros:gestionar",
        "evaluaciones:gestionar",
        "guardias:registrar",
        "tareas:gestionar",
        "avisos:publicar",
        "equipos:asignar",
        "estructura:gestionar",
        "usuarios:gestionar",
        "auditoria:ver",
        "tenant:configurar",
        "impersonacion:usar",
        "inbox:leer",
        "inbox:responder",
    ],
    "FINANZAS": [
        "avisos:confirmar",
        "auditoria:ver",
        "liquidaciones:grilla",
        "liquidaciones:cerrar",
        "facturas:gestionar",
        "inbox:leer",
        "inbox:responder",
    ],
}


def _parse_key(key: str) -> tuple[str, str]:
    modulo, accion = key.split(":", 1)
    return modulo, accion


def _all_permission_keys() -> set[str]:
    keys: set[str] = set()
    for perms in ROLE_PERMISSION_KEYS.values():
        keys.update(perms)
    return keys


async def seed_tenant_rbac(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    """Seed idempotente async (tests y tenants nuevos)."""
    permiso_ids: dict[str, uuid.UUID] = {}
    for key in sorted(_all_permission_keys()):
        modulo, accion = _parse_key(key)
        existing = await session.execute(
            select(Permiso.id).where(
                Permiso.tenant_id == tenant_id,
                Permiso.modulo == modulo,
                Permiso.accion == accion,
                Permiso.deleted_at.is_(None),
            )
        )
        perm_id = existing.scalar_one_or_none()
        if perm_id is None:
            perm = Permiso(tenant_id=tenant_id, modulo=modulo, accion=accion)
            session.add(perm)
            await session.flush()
            perm_id = perm.id
        permiso_ids[key] = perm_id

    rol_ids: dict[str, uuid.UUID] = {}
    for codigo, nombre in DOMAIN_ROLES.items():
        existing = await session.execute(
            select(Rol.id).where(
                Rol.tenant_id == tenant_id,
                Rol.codigo == codigo,
                Rol.deleted_at.is_(None),
            )
        )
        rol_id = existing.scalar_one_or_none()
        if rol_id is None:
            rol = Rol(tenant_id=tenant_id, codigo=codigo, nombre=nombre)
            session.add(rol)
            await session.flush()
            rol_id = rol.id
        rol_ids[codigo] = rol_id

    for codigo_rol, keys in ROLE_PERMISSION_KEYS.items():
        rol_id = rol_ids[codigo_rol]
        for key in keys:
            permiso_id = permiso_ids[key]
            link = await session.execute(
                select(RolPermiso.id).where(
                    RolPermiso.tenant_id == tenant_id,
                    RolPermiso.rol_id == rol_id,
                    RolPermiso.permiso_id == permiso_id,
                    RolPermiso.deleted_at.is_(None),
                )
            )
            if link.scalar_one_or_none() is None:
                session.add(
                    RolPermiso(
                        tenant_id=tenant_id, rol_id=rol_id, permiso_id=permiso_id
                    )
                )
    await session.flush()


def seed_tenant_rbac_sync(conn: Connection, tenant_id: uuid.UUID) -> None:
    """Seed idempotente sync (Alembic migración 003)."""
    permiso_ids: dict[str, uuid.UUID] = {}
    for key in sorted(_all_permission_keys()):
        modulo, accion = _parse_key(key)
        row = conn.execute(
            text(
                """
                SELECT id FROM permisos
                WHERE tenant_id = :tenant_id AND modulo = :modulo AND accion = :accion
                  AND deleted_at IS NULL
                """
            ),
            {"tenant_id": tenant_id, "modulo": modulo, "accion": accion},
        ).fetchone()
        if row:
            permiso_ids[key] = row[0]
        else:
            perm_id = uuid.uuid4()
            conn.execute(
                text(
                    """
                    INSERT INTO permisos (id, tenant_id, modulo, accion)
                    VALUES (:id, :tenant_id, :modulo, :accion)
                    """
                ),
                {
                    "id": perm_id,
                    "tenant_id": tenant_id,
                    "modulo": modulo,
                    "accion": accion,
                },
            )
            permiso_ids[key] = perm_id

    rol_ids: dict[str, uuid.UUID] = {}
    for codigo, nombre in DOMAIN_ROLES.items():
        row = conn.execute(
            text(
                """
                SELECT id FROM roles
                WHERE tenant_id = :tenant_id AND codigo = :codigo AND deleted_at IS NULL
                """
            ),
            {"tenant_id": tenant_id, "codigo": codigo},
        ).fetchone()
        if row:
            rol_ids[codigo] = row[0]
        else:
            rol_id = uuid.uuid4()
            conn.execute(
                text(
                    """
                    INSERT INTO roles (id, tenant_id, codigo, nombre)
                    VALUES (:id, :tenant_id, :codigo, :nombre)
                    """
                ),
                {
                    "id": rol_id,
                    "tenant_id": tenant_id,
                    "codigo": codigo,
                    "nombre": nombre,
                },
            )
            rol_ids[codigo] = rol_id

    for codigo_rol, keys in ROLE_PERMISSION_KEYS.items():
        rol_id = rol_ids[codigo_rol]
        for key in keys:
            permiso_id = permiso_ids[key]
            exists = conn.execute(
                text(
                    """
                    SELECT id FROM roles_permisos
                    WHERE tenant_id = :tenant_id AND rol_id = :rol_id
                      AND permiso_id = :permiso_id AND deleted_at IS NULL
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "rol_id": rol_id,
                    "permiso_id": permiso_id,
                },
            ).fetchone()
            if exists is None:
                conn.execute(
                    text(
                        """
                        INSERT INTO roles_permisos (id, tenant_id, rol_id, permiso_id)
                        VALUES (:id, :tenant_id, :rol_id, :permiso_id)
                        """
                    ),
                    {
                        "id": uuid.uuid4(),
                        "tenant_id": tenant_id,
                        "rol_id": rol_id,
                        "permiso_id": permiso_id,
                    },
                )
