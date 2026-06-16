"""Servicio de usuarios — C-07.

Reglas clave:
- PII (dni, cuil, cbu, alias_cbu) solo se persiste a través de `actualizar_pii`.
- Los logs NUNCA deben incluir PII; este servicio no loguea esos campos.
- `desactivar_usuario` usa soft delete (deleted_at), no borra el registro.
- La identidad (tenant_id) viene siempre del contexto, nunca del body.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import email_blind_index, hash_password
from app.models.usuario import Usuario, UsuarioEstado
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioPIIUpdate, UsuarioUpdate

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = UsuarioRepository(session, tenant_id)

    async def crear_usuario(self, data: UsuarioCreate) -> Usuario:
        email_hash = email_blind_index(data.email)
        usuario = Usuario(
            nombre=data.nombre,
            apellidos=data.apellidos,
            email=data.email,
            email_hash=email_hash,
            password_hash=hash_password(data.password),
            banco=data.banco,
            regional=data.regional,
            legajo=data.legajo,
            legajo_profesional=data.legajo_profesional,
            facturador=data.facturador,
            estado=UsuarioEstado.activo,
        )
        await self._repo.add(usuario)
        logger.info("usuario creado id=%s", usuario.id)
        return usuario

    async def actualizar_usuario(
        self, usuario_id: uuid.UUID, data: UsuarioUpdate
    ) -> Usuario | None:
        usuario = await self._repo.get(usuario_id)
        if usuario is None:
            return None
        if data.nombre is not None:
            usuario.nombre = data.nombre
        if data.apellidos is not None:
            usuario.apellidos = data.apellidos
        if data.banco is not None:
            usuario.banco = data.banco
        if data.regional is not None:
            usuario.regional = data.regional
        if data.legajo is not None:
            usuario.legajo = data.legajo
        if data.legajo_profesional is not None:
            usuario.legajo_profesional = data.legajo_profesional
        if data.facturador is not None:
            usuario.facturador = data.facturador
        if data.estado is not None:
            usuario.estado = data.estado
        logger.info("usuario actualizado id=%s", usuario_id)
        return usuario

    async def actualizar_pii(
        self, usuario_id: uuid.UUID, data: UsuarioPIIUpdate
    ) -> Usuario | None:
        usuario = await self._repo.get(usuario_id)
        if usuario is None:
            return None
        if data.dni is not None:
            usuario.dni = data.dni
        if data.cuil is not None:
            usuario.cuil = data.cuil
        if data.cbu is not None:
            usuario.cbu = data.cbu
        if data.alias_cbu is not None:
            usuario.alias_cbu = data.alias_cbu
        return usuario

    async def desactivar_usuario(self, usuario_id: uuid.UUID) -> bool:
        usuario = await self._repo.get(usuario_id)
        if usuario is None:
            return False
        usuario.estado = UsuarioEstado.inactivo
        usuario.is_active = False
        await self._repo.soft_delete(usuario)
        logger.info("usuario desactivado id=%s", usuario_id)
        return True

    async def get(self, usuario_id: uuid.UUID) -> Usuario | None:
        return await self._repo.get(usuario_id)

    async def list_activos(self) -> list[Usuario]:
        return list(await self._repo.list(estado=UsuarioEstado.activo))
