"""Repositorios de refresh y reset tokens (tenant-scoped)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PasswordResetToken, RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Busca por hash dentro del tenant (revocado o no, para detección de reuso)."""
        result = await self.session.execute(
            self._base_query().where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_hash_global(
        session: AsyncSession, token_hash: str
    ) -> RefreshToken | None:
        """Resuelve refresh opaco sin tenant previo (endpoint público /refresh)."""
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke(
        self, token: RefreshToken, *, replaced_by_id: uuid.UUID | None = None
    ) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        token.replaced_by_id = replaced_by_id
        await self.session.flush()

    async def revoke_all_for_user(self, usuario_id: uuid.UUID) -> None:
        """Invalida toda la cadena de refresh del usuario (detección de robo)."""
        await self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.tenant_id == self.tenant_id,
                RefreshToken.usuario_id == usuario_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.flush()


class PasswordResetTokenRepository(BaseRepository[PasswordResetToken]):
    model = PasswordResetToken

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.session.execute(
            self._base_query().where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: PasswordResetToken) -> None:
        token.used_at = datetime.now(timezone.utc)
        await self.session.flush()
