"""Repositorios del catálogo RBAC (tenant-scoped)."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select

from app.models import Permiso, Rol, RolPermiso, UsuarioRol
from app.repositories.base import BaseRepository


class RolRepository(BaseRepository[Rol]):
    model = Rol

    async def get_by_codigo(self, codigo: str) -> Rol | None:
        result = await self.session.execute(
            self._base_query().where(Rol.codigo == codigo)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[Rol]:
        result = await self.session.execute(
            self._base_query().order_by(Rol.codigo)
        )
        return result.scalars().all()


class PermisoRepository(BaseRepository[Permiso]):
    model = Permiso

    async def list_all(self) -> Sequence[Permiso]:
        result = await self.session.execute(
            self._base_query().order_by(Permiso.modulo, Permiso.accion)
        )
        return result.scalars().all()


class RolPermisoRepository(BaseRepository[RolPermiso]):
    model = RolPermiso

    async def permission_keys_for_roles(self, role_codes: Sequence[str]) -> set[str]:
        if not role_codes:
            return set()
        result = await self.session.execute(
            select(Permiso.modulo, Permiso.accion)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .join(Rol, Rol.id == RolPermiso.rol_id)
            .where(
                RolPermiso.tenant_id == self.tenant_id,
                RolPermiso.deleted_at.is_(None),
                Permiso.tenant_id == self.tenant_id,
                Permiso.deleted_at.is_(None),
                Rol.tenant_id == self.tenant_id,
                Rol.deleted_at.is_(None),
                Rol.codigo.in_(list(role_codes)),
            )
        )
        return {f"{modulo}:{accion}" for modulo, accion in result.all()}


class UsuarioRolRepository(BaseRepository[UsuarioRol]):
    model = UsuarioRol

    async def list_role_codes_for_user(self, usuario_id: uuid.UUID) -> list[str]:
        result = await self.session.execute(
            select(Rol.codigo)
            .join(UsuarioRol, UsuarioRol.rol_id == Rol.id)
            .where(
                UsuarioRol.tenant_id == self.tenant_id,
                UsuarioRol.usuario_id == usuario_id,
                UsuarioRol.deleted_at.is_(None),
                Rol.tenant_id == self.tenant_id,
                Rol.deleted_at.is_(None),
            )
            .order_by(Rol.codigo)
        )
        return list(result.scalars().all())

    async def assign_role(self, usuario_id: uuid.UUID, rol_id: uuid.UUID) -> UsuarioRol:
        link = UsuarioRol(usuario_id=usuario_id, rol_id=rol_id)
        return await self.add(link)
