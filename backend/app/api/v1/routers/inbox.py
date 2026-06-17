"""Endpoints de bandeja de mensajes internos — C-20 (F3.4, FL-10)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.inbox import (
    HiloDetalleResponse,
    HiloListResponse,
    MensajeCreadoResponse,
    MensajeCreate,
    MensajeResponder,
    MensajeResponse,
)
from app.services.inbox_service import InboxService

router = APIRouter(prefix="/api/inbox", tags=["inbox"])
_LEER = [Depends(require_permission("inbox:leer"))]
_RESPONDER = [Depends(require_permission("inbox:responder"))]


@router.post(
    "/mensajes",
    response_model=MensajeCreadoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_RESPONDER,
)
async def enviar_mensaje(
    payload: MensajeCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MensajeCreadoResponse:
    try:
        result = await InboxService(db, user.tenant_id).enviar_mensaje(
            remitente_id=user.id,
            destinatario_id=payload.destinatario_id,
            asunto=payload.asunto,
            cuerpo=payload.cuerpo,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    await db.commit()
    return result


@router.get("/hilos", response_model=HiloListResponse, dependencies=_LEER)
async def listar_hilos(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HiloListResponse:
    return await InboxService(db, user.tenant_id).listar_hilos(user.id)


@router.get(
    "/hilos/{hilo_id}",
    response_model=HiloDetalleResponse,
    dependencies=_LEER,
)
async def obtener_hilo(
    hilo_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HiloDetalleResponse:
    detalle = await InboxService(db, user.tenant_id).obtener_hilo(hilo_id, user.id)
    if detalle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hilo no encontrado")
    return detalle


@router.post(
    "/hilos/{hilo_id}/responder",
    response_model=MensajeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_RESPONDER,
)
async def responder_hilo(
    hilo_id: uuid.UUID,
    payload: MensajeResponder,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MensajeResponse:
    mensaje = await InboxService(db, user.tenant_id).responder(
        hilo_id, user.id, payload.cuerpo
    )
    if mensaje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hilo no encontrado")
    await db.commit()
    return mensaje
