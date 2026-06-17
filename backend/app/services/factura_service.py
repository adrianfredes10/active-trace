"""Servicio de facturas (C-18)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.liquidacion import Factura, FacturaEstado
from app.repositories.factura_repository import FacturaRepository
from app.repositories.usuario_repository import UsuarioRepository


class FacturaNoEncontradaError(ValueError):
    pass


class FacturaService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.repo = FacturaRepository(session, tenant_id)
        self.usuario_repo = UsuarioRepository(session, tenant_id)

    async def crear(
        self,
        usuario_id: uuid.UUID,
        periodo: str,
        detalle: str,
        referencia_archivo: str | None,
        tamano_kb: Decimal | None,
    ) -> Factura:
        usuario = await self.usuario_repo.get(usuario_id)
        if usuario is None:
            raise ValueError("Usuario no encontrado")
        if not usuario.facturador:
            raise ValueError("El usuario no está marcado como facturador")
        return await self.repo.add(
            Factura(
                usuario_id=usuario_id,
                periodo=periodo,
                detalle=detalle,
                referencia_archivo=referencia_archivo,
                tamano_kb=tamano_kb,
                estado=FacturaEstado.pendiente,
                cargada_at=datetime.now(timezone.utc),
            )
        )

    async def listar(self, periodo: str | None = None) -> list[Factura]:
        return list(await self.repo.list_periodo(periodo))

    async def marcar_abonada(self, factura_id: uuid.UUID) -> Factura:
        factura = await self.repo.get(factura_id)
        if factura is None:
            raise FacturaNoEncontradaError("Factura no encontrada")
        factura.estado = FacturaEstado.abonada
        factura.abonada_at = datetime.now(timezone.utc)
        await self.session.flush()
        return factura

    @staticmethod
    def to_response(f: Factura) -> dict:
        tam = None if f.tamano_kb is None else format(f.tamano_kb.quantize(Decimal("0.01")), "f")
        return {
            "id": f.id,
            "usuario_id": f.usuario_id,
            "periodo": f.periodo,
            "detalle": f.detalle,
            "referencia_archivo": f.referencia_archivo,
            "tamano_kb": tam,
            "estado": f.estado.value,
            "cargada_at": f.cargada_at,
            "abonada_at": f.abonada_at,
        }
