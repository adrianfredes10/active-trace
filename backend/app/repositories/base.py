"""Repository genérico con scope de tenant SIEMPRE activo (ADR-002 row-level).

Invariante de seguridad: no existe forma en esta API de ejecutar una query
de dominio sin filtrar por `tenant_id`. Todo método filtra además los
registros soft-deleted (`deleted_at IS NULL`) por defecto.
"""

import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import TenantScopedMixin

ModelT = TypeVar("ModelT", bound=TenantScopedMixin)


class BaseRepository(Generic[ModelT]):
    #: Las subclases de dominio fijan el modelo aquí.
    model: type[ModelT]

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        model: type[ModelT] | None = None,
    ) -> None:
        resolved = model or getattr(self, "model", None)
        if resolved is None:
            raise ValueError("BaseRepository requiere un modelo")
        self.session = session
        self.tenant_id = tenant_id
        self.model = resolved

    def _base_query(self) -> Any:
        return select(self.model).where(
            self.model.tenant_id == self.tenant_id,
            self.model.deleted_at.is_(None),
        )

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        result = await self.session.execute(
            self._base_query().where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def list(self, **filters: Any) -> Sequence[ModelT]:
        query = self._base_query()
        for field, value in filters.items():
            query = query.where(getattr(self.model, field) == value)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def add(self, entity: ModelT) -> ModelT:
        # La identidad de tenant la define el contexto, no el dato de entrada.
        entity.tenant_id = self.tenant_id
        now = datetime.now(timezone.utc)
        if entity.created_at is None:
            entity.created_at = now
        if entity.updated_at is None:
            entity.updated_at = now
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def soft_delete(self, entity: ModelT) -> None:
        entity.deleted_at = datetime.now(timezone.utc)
        await self.session.flush()

    async def get_including_deleted(self, entity_id: uuid.UUID) -> ModelT | None:
        """Escape hatch explícito para auditoría/restore: incluye borrados."""
        result = await self.session.execute(
            select(self.model).where(
                self.model.tenant_id == self.tenant_id,
                self.model.id == entity_id,
            )
        )
        return result.scalar_one_or_none()
