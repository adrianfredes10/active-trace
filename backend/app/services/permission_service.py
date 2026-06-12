"""Resolución de permisos efectivos server-side (C-04)."""

import uuid
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.rbac_repository import RolPermisoRepository


class PermissionService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.rol_permisos = RolPermisoRepository(session, tenant_id)

    async def effective_permissions(self, role_codes: Sequence[str]) -> frozenset[str]:
        keys = await self.rol_permisos.permission_keys_for_roles(role_codes)
        return frozenset(keys)
