"""Endpoints de asignaciones — C-07.

Guard: `equipos:asignar` (COORDINADOR / ADMIN).
Flujo: Router → AsignacionService → AsignacionRepository → Asignacion.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.asignacion import (
    AsignacionCreate,
    AsignacionListResponse,
    AsignacionResponse,
    AsignacionUpdate,
    asignacion_response,
)
from app.services.asignacion_service import AsignacionService
from app.services.audit_service import AuditContext, AuditService

router = APIRouter(
    prefix="/api/asignaciones",
    tags=["asignaciones"],
    dependencies=[Depends(require_permission("equipos:asignar"))],
)


async def _audit(
    db: AsyncSession,
    user: CurrentUser,
    request: Request,
    *,
    accion: AuditAction,
    detalle: dict,
    materia_id: uuid.UUID | None = None,
) -> None:
    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=accion,
        detalle=detalle,
        materia_id=materia_id,
    )


@router.get("", response_model=AsignacionListResponse)
async def listar_asignaciones(
    usuario_id: uuid.UUID | None = None,
    materia_id: uuid.UUID | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsignacionListResponse:
    svc = AsignacionService(db, user.tenant_id)
    if usuario_id is not None:
        items = await svc.list_vigentes_by_usuario(usuario_id)
    elif materia_id is not None:
        items = await svc.list_vigentes_by_materia(materia_id)
    else:
        items = await svc.list_all()
    return AsignacionListResponse(items=[asignacion_response(a) for a in items])


@router.post("", response_model=AsignacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_asignacion(
    body: AsignacionCreate,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionResponse:
    svc = AsignacionService(db, user.tenant_id)
    try:
        nueva = await svc.crear_asignacion(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    await _audit(
        db,
        user,
        request,
        accion=AuditAction.ASIGNACION_CREAR,
        detalle={"asignacion_id": str(nueva.id), "rol": nueva.rol.value},
        materia_id=nueva.materia_id,
    )
    await db.commit()
    await db.refresh(nueva)
    return asignacion_response(nueva)


@router.get("/{asignacion_id}", response_model=AsignacionResponse)
async def obtener_asignacion(
    asignacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionResponse:
    svc = AsignacionService(db, user.tenant_id)
    a = await svc.get(asignacion_id)
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    return asignacion_response(a)


@router.put("/{asignacion_id}", response_model=AsignacionResponse)
async def actualizar_asignacion(
    asignacion_id: uuid.UUID,
    body: AsignacionUpdate,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AsignacionResponse:
    svc = AsignacionService(db, user.tenant_id)
    try:
        a = await svc.actualizar_vigencia(asignacion_id, body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if a is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")

    await _audit(
        db,
        user,
        request,
        accion=AuditAction.ASIGNACION_MODIFICAR,
        detalle={"asignacion_id": str(asignacion_id)},
        materia_id=a.materia_id,
    )
    await db.commit()
    await db.refresh(a)
    return asignacion_response(a)


@router.delete("/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def anular_asignacion(
    asignacion_id: uuid.UUID,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = AsignacionService(db, user.tenant_id)
    asig = await svc.get(asignacion_id)
    if asig is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    await svc.anular_asignacion(asignacion_id)

    await _audit(
        db,
        user,
        request,
        accion=AuditAction.ASIGNACION_ANULAR,
        detalle={"asignacion_id": str(asignacion_id)},
        materia_id=asig.materia_id,
    )
    await db.commit()
