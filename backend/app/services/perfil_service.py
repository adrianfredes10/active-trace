"""Servicio de perfil propio — C-20 (F11.1)."""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.perfil import PerfilUpdate

logger = logging.getLogger(__name__)


class PerfilService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self._repo = UsuarioRepository(session, tenant_id)

    async def obtener(self, usuario_id: uuid.UUID) -> Usuario | None:
        return await self._repo.get(usuario_id)

    async def actualizar(
        self, usuario_id: uuid.UUID, data: PerfilUpdate
    ) -> Usuario | None:
        usuario = await self._repo.get(usuario_id)
        if usuario is None:
            return None
        if data.nombre is not None:
            usuario.nombre = data.nombre
        if data.apellidos is not None:
            usuario.apellidos = data.apellidos
        if data.dni is not None:
            usuario.dni = data.dni
        if data.banco is not None:
            usuario.banco = data.banco
        if data.cbu is not None:
            usuario.cbu = data.cbu
        if data.alias_cbu is not None:
            usuario.alias_cbu = data.alias_cbu
        if data.regional is not None:
            usuario.regional = data.regional
        if data.legajo_profesional is not None:
            usuario.legajo_profesional = data.legajo_profesional
        if data.facturador is not None:
            usuario.facturador = data.facturador
        logger.info("perfil actualizado usuario_id=%s", usuario_id)
        return usuario
