"""Repository de facturas (C-18)."""

import uuid
from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select

from app.models.liquidacion import Factura, FacturaEstado
from app.repositories.base import BaseRepository


class FacturaRepository(BaseRepository[Factura]):
    model = Factura

    async def list_periodo(self, periodo: str | None = None) -> Sequence[Factura]:
        query = self._base_query().order_by(Factura.cargada_at.desc())
        if periodo is not None:
            query = query.where(Factura.periodo == periodo)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def sum_periodo(self, periodo: str) -> Decimal:
        """Suma importes de facturas del período (placeholder: cuenta 1 por factura)."""
        result = await self.session.execute(
            select(func.count(Factura.id)).where(
                Factura.tenant_id == self.tenant_id,
                Factura.deleted_at.is_(None),
                Factura.periodo == periodo,
            )
        )
        count = result.scalar_one()
        return Decimal(count)
