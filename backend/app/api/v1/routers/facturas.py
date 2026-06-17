"""Endpoints de facturas — C-18."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.factura import FacturaCreate, FacturaListResponse, FacturaResponse
from app.services.factura_service import FacturaNoEncontradaError, FacturaService

router = APIRouter(prefix="/api/facturas", tags=["facturas"])
_GESTIONAR = [Depends(require_permission("facturas:gestionar"))]


@router.get("", response_model=FacturaListResponse, dependencies=_GESTIONAR)
async def listar_facturas(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    periodo: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
) -> FacturaListResponse:
    svc = FacturaService(db, user.tenant_id)
    items = await svc.listar(periodo)
    return FacturaListResponse(
        items=[FacturaResponse(**svc.to_response(f)) for f in items]
    )


@router.post(
    "",
    response_model=FacturaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GESTIONAR,
)
async def crear_factura(
    body: FacturaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FacturaResponse:
    svc = FacturaService(db, user.tenant_id)
    try:
        f = await svc.crear(
            body.usuario_id,
            body.periodo,
            body.detalle,
            body.referencia_archivo,
            body.tamano_kb,
        )
        await db.commit()
        return FacturaResponse(**svc.to_response(f))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc


@router.post(
    "/{factura_id}/abonar",
    response_model=FacturaResponse,
    dependencies=_GESTIONAR,
)
async def abonar_factura(
    factura_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FacturaResponse:
    svc = FacturaService(db, user.tenant_id)
    try:
        f = await svc.marcar_abonada(factura_id)
        await db.commit()
        return FacturaResponse(**svc.to_response(f))
    except FacturaNoEncontradaError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
