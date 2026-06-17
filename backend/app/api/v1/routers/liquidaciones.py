"""Endpoints de liquidaciones — C-18."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.liquidacion import (
    GrillaListResponse,
    LiquidacionItemResponse,
    LiquidacionKpisResponse,
    LiquidacionListResponse,
    SalarioBaseCreate,
    SalarioBaseResponse,
    SalarioPlusCreate,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.liquidacion_service import (
    LiquidacionCerradaError,
    LiquidacionNoEncontradaError,
    LiquidacionService,
)

router = APIRouter(prefix="/api/liquidaciones", tags=["liquidaciones"])
_GRILLA = [Depends(require_permission("liquidaciones:grilla"))]
_CERRAR = [Depends(require_permission("liquidaciones:cerrar"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, LiquidacionCerradaError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, (LiquidacionNoEncontradaError, ValueError)):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


def _base_response(b: object) -> SalarioBaseResponse:
    return SalarioBaseResponse(
        id=b.id,
        rol=b.rol.value if hasattr(b.rol, "value") else str(b.rol),
        monto=format(b.monto, "f"),
        vig_desde=b.vig_desde,
        vig_hasta=b.vig_hasta,
    )


@router.get("", response_model=LiquidacionListResponse, dependencies=_GRILLA)
async def listar_liquidaciones(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    periodo: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    segmento: str = Query("general", pattern=r"^(general|nexo|factura)$"),
) -> LiquidacionListResponse:
    svc = LiquidacionService(db, user.tenant_id)
    items = await svc.listar(periodo, segmento)
    await db.commit()
    return LiquidacionListResponse(
        items=[LiquidacionItemResponse(**svc.to_item_response(i)) for i in items]
    )


@router.get("/kpis", response_model=LiquidacionKpisResponse, dependencies=_GRILLA)
async def kpis_liquidaciones(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    periodo: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
) -> LiquidacionKpisResponse:
    svc = LiquidacionService(db, user.tenant_id)
    data = await svc.kpis(periodo)
    await db.commit()
    return LiquidacionKpisResponse(**data)


@router.post(
    "/{liquidacion_id}/cerrar",
    response_model=LiquidacionItemResponse,
    dependencies=_CERRAR,
)
async def cerrar_liquidacion(
    liquidacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LiquidacionItemResponse:
    svc = LiquidacionService(db, user.tenant_id)
    try:
        liq = await svc.cerrar(liquidacion_id)
        await AuditService(db, user.tenant_id).record(
            AuditContext.from_user(user),
            accion=AuditAction.LIQUIDACION_CERRAR,
            detalle={"liquidacion_id": str(liquidacion_id), "periodo": liq.periodo},
        )
        await db.commit()
        return LiquidacionItemResponse(**svc.to_item_response(liq))
    except (LiquidacionCerradaError, LiquidacionNoEncontradaError, ValueError) as exc:
        raise _http_error(exc) from exc


@router.get("/grilla", response_model=GrillaListResponse, dependencies=_GRILLA)
async def listar_grilla(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GrillaListResponse:
    svc = LiquidacionService(db, user.tenant_id)
    items = await svc.listar_grilla()
    return GrillaListResponse(items=[_base_response(i) for i in items])


@router.post(
    "/grilla/base",
    response_model=SalarioBaseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GRILLA,
)
async def crear_salario_base(
    body: SalarioBaseCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SalarioBaseResponse:
    svc = LiquidacionService(db, user.tenant_id)
    try:
        row = await svc.crear_salario_base(body.rol, body.monto, body.vig_desde)
        await db.commit()
        return _base_response(row)
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/grilla/plus",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GRILLA,
)
async def crear_salario_plus(
    body: SalarioPlusCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    svc = LiquidacionService(db, user.tenant_id)
    try:
        row = await svc.crear_salario_plus(
            body.grupo, body.rol, body.monto, body.vig_desde, body.descripcion
        )
        await db.commit()
        return {
            "id": row.id,
            "grupo": row.grupo,
            "rol": row.rol.value,
            "monto": format(row.monto, "f"),
            "vig_desde": row.vig_desde.isoformat(),
            "vig_hasta": row.vig_hasta.isoformat() if row.vig_hasta else None,
        }
    except ValueError as exc:
        raise _http_error(exc) from exc
