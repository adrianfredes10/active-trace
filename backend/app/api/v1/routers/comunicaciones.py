"""Endpoints de comunicaciones salientes — C-12."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.comunicacion import (
    AprobarComunicacionResponse,
    CancelarComunicacionResponse,
    ComunicacionEnviarRequest,
    ComunicacionEnviarResponse,
    ComunicacionPreviewRequest,
    ComunicacionPreviewResponse,
    ComunicacionResponse,
    LoteComunicacionResponse,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.comunicacion_service import ComunicacionService

router = APIRouter(prefix="/api/comunicaciones", tags=["comunicaciones"])


def _item_response(item: object) -> ComunicacionResponse:
    return ComunicacionResponse(
        id=item.id,
        materia_id=item.materia_id,
        asunto=item.asunto,
        estado=item.estado.value if hasattr(item.estado, "value") else str(item.estado),
        lote_id=item.lote_id,
        es_masivo=item.es_masivo,
        aprobado=item.aprobado,
        enviado_at=item.enviado_at,
    )


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


@router.post(
    "/preview",
    response_model=ComunicacionPreviewResponse,
    dependencies=[Depends(require_permission("comunicacion:enviar"))],
)
async def preview_comunicacion(
    body: ComunicacionPreviewRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComunicacionPreviewResponse:
    svc = ComunicacionService(db, user.tenant_id)
    resultado = svc.preview(
        asunto=body.asunto,
        cuerpo=body.cuerpo,
        muestra=body.muestra.model_dump(),
    )
    return ComunicacionPreviewResponse(**resultado)


@router.post(
    "/enviar",
    response_model=ComunicacionEnviarResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("comunicacion:enviar"))],
)
async def enviar_comunicaciones(
    body: ComunicacionEnviarRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComunicacionEnviarResponse:
    svc = ComunicacionService(db, user.tenant_id)
    try:
        resultado = await svc.encolar(
            user=user,
            materia_id=body.materia_id,
            asunto=body.asunto,
            cuerpo=body.cuerpo,
            destinatarios=[d.model_dump() for d in body.destinatarios],
            confirmo_preview=body.confirmo_preview,
        )
    except ValueError as exc:
        raise _http_error(exc) from exc

    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.COMUNICACION_ENVIAR,
        detalle={
            "lote_id": str(resultado["lote_id"]),
            "encoladas": resultado["encoladas"],
            "requiere_aprobacion": resultado["requiere_aprobacion"],
        },
        materia_id=body.materia_id,
        filas_afectadas=resultado["encoladas"],
    )
    await db.commit()
    return ComunicacionEnviarResponse(
        lote_id=resultado["lote_id"],
        encoladas=resultado["encoladas"],
        requiere_aprobacion=resultado["requiere_aprobacion"],
        items=[_item_response(i) for i in resultado["items"]],
    )


@router.get(
    "/lotes/{lote_id}",
    response_model=LoteComunicacionResponse,
    dependencies=[Depends(require_permission("comunicacion:enviar"))],
)
async def obtener_lote(
    lote_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoteComunicacionResponse:
    items = await ComunicacionService(db, user.tenant_id).listar_lote(lote_id)
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote no encontrado")
    return LoteComunicacionResponse(
        lote_id=lote_id,
        total=len(items),
        items=[_item_response(i) for i in items],
    )


@router.post(
    "/lotes/{lote_id}/aprobar",
    response_model=AprobarComunicacionResponse,
    dependencies=[Depends(require_permission("comunicacion:aprobar"))],
)
async def aprobar_lote(
    lote_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AprobarComunicacionResponse:
    try:
        count = await ComunicacionService(db, user.tenant_id).aprobar_lote(lote_id, user)
    except ValueError as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return AprobarComunicacionResponse(aprobadas=count)


@router.post(
    "/{comunicacion_id}/aprobar",
    response_model=ComunicacionResponse,
    dependencies=[Depends(require_permission("comunicacion:aprobar"))],
)
async def aprobar_individual(
    comunicacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComunicacionResponse:
    try:
        item = await ComunicacionService(db, user.tenant_id).aprobar_individual(
            comunicacion_id, user
        )
    except ValueError as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return _item_response(item)


@router.post(
    "/{comunicacion_id}/cancelar",
    response_model=ComunicacionResponse,
    dependencies=[Depends(require_permission("comunicacion:enviar"))],
)
async def cancelar_comunicacion(
    comunicacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComunicacionResponse:
    try:
        item = await ComunicacionService(db, user.tenant_id).cancelar(comunicacion_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return _item_response(item)


@router.post(
    "/lotes/{lote_id}/cancelar",
    response_model=CancelarComunicacionResponse,
    dependencies=[Depends(require_permission("comunicacion:enviar"))],
)
async def cancelar_lote(
    lote_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CancelarComunicacionResponse:
    count = await ComunicacionService(db, user.tenant_id).cancelar_lote(lote_id)
    await db.commit()
    return CancelarComunicacionResponse(canceladas=count)
