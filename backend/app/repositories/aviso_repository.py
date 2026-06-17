"""Repository de avisos — C-15."""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select

from app.models.aviso import AcknowledgmentAviso, Aviso
from app.repositories.base import BaseRepository


class AvisoRepository(BaseRepository[Aviso]):
    model = Aviso

    async def list_activos(self) -> Sequence[Aviso]:
        result = await self.session.execute(
            self._base_query()
            .where(Aviso.activo.is_(True))
            .order_by(Aviso.orden.desc(), Aviso.created_at.desc())
        )
        return result.scalars().all()

    async def list_gestion(self) -> Sequence[Aviso]:
        result = await self.session.execute(
            self._base_query().order_by(Aviso.orden.desc(), Aviso.created_at.desc())
        )
        return result.scalars().all()


class AcknowledgmentAvisoRepository(BaseRepository[AcknowledgmentAviso]):
    model = AcknowledgmentAviso

    async def get_by_aviso_usuario(
        self, aviso_id: uuid.UUID, usuario_id: uuid.UUID
    ) -> AcknowledgmentAviso | None:
        result = await self.session.execute(
            self._base_query().where(
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.usuario_id == usuario_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_aviso(self, aviso_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(AcknowledgmentAviso)
            .where(
                AcknowledgmentAviso.tenant_id == self.tenant_id,
                AcknowledgmentAviso.aviso_id == aviso_id,
                AcknowledgmentAviso.deleted_at.is_(None),
            )
        )
        return int(result.scalar_one())

    async def list_by_aviso(
        self, aviso_id: uuid.UUID
    ) -> Sequence[AcknowledgmentAviso]:
        result = await self.session.execute(
            self._base_query().where(AcknowledgmentAviso.aviso_id == aviso_id)
        )
        return result.scalars().all()
