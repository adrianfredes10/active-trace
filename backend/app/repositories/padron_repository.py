"""Repository de padrón versionado (tenant-scoped)."""

import uuid
from collections.abc import Sequence

from sqlalchemy import update

from app.models.padron import EntradaPadron, VersionPadron
from app.repositories.base import BaseRepository


class VersionPadronRepository(BaseRepository[VersionPadron]):
    model = VersionPadron

    async def get_activa(
        self, materia_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> VersionPadron | None:
        result = await self.session.execute(
            self._base_query()
            .where(VersionPadron.materia_id == materia_id)
            .where(VersionPadron.cohorte_id == cohorte_id)
            .where(VersionPadron.activa.is_(True))
        )
        return result.scalar_one_or_none()

    async def desactivar_contexto(
        self, materia_id: uuid.UUID, cohorte_id: uuid.UUID
    ) -> int:
        result = await self.session.execute(
            update(VersionPadron)
            .where(
                VersionPadron.tenant_id == self.tenant_id,
                VersionPadron.materia_id == materia_id,
                VersionPadron.cohorte_id == cohorte_id,
                VersionPadron.activa.is_(True),
                VersionPadron.deleted_at.is_(None),
            )
            .values(activa=False)
        )
        return result.rowcount or 0

    async def list_by_cargador_materia(
        self, cargado_por: uuid.UUID, materia_id: uuid.UUID
    ) -> Sequence[VersionPadron]:
        result = await self.session.execute(
            self._base_query()
            .where(VersionPadron.cargado_por == cargado_por)
            .where(VersionPadron.materia_id == materia_id)
        )
        return result.scalars().all()


class EntradaPadronRepository(BaseRepository[EntradaPadron]):
    model = EntradaPadron

    async def list_by_version(self, version_id: uuid.UUID) -> Sequence[EntradaPadron]:
        result = await self.session.execute(
            self._base_query().where(EntradaPadron.version_id == version_id)
        )
        return result.scalars().all()

    async def add_many(self, entradas: list[EntradaPadron]) -> list[EntradaPadron]:
        for entrada in entradas:
            entrada.tenant_id = self.tenant_id
            self.session.add(entrada)
        await self.session.flush()
        return entradas
