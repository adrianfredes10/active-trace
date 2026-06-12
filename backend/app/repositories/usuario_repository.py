"""Repository de usuarios (tenant-scoped). Lookup por blind index de email."""

from app.models import Usuario
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    model = Usuario

    async def get_by_email_hash(self, email_hash: str) -> Usuario | None:
        result = await self.session.execute(
            self._base_query().where(Usuario.email_hash == email_hash)
        )
        return result.scalar_one_or_none()
