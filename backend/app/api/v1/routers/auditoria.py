"""Panel de auditoría y métricas — C-19 (F9.1, F9.2)."""

import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.audit import AuditLogItem
from app.schemas.auditoria import (
    AccionPorDiaItem,
    AccionesPorDiaResponse,
    AuditoriaLogResponse,
    ComunicacionEstadoItem,
    ComunicacionesPorDocenteResponse,
    InteraccionItem,
    InteraccionesResponse,
)
from app.services.auditoria_panel_service import AuditoriaPanelService

router = APIRouter(prefix="/api/auditoria", tags=["auditoria"])
_GUARD = [Depends(require_permission("auditoria:ver"))]


def _http_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _log_item(r: object) -> AuditLogItem:
    return AuditLogItem(
        id=r.id,
        fecha_hora=r.fecha_hora,
        actor_id=r.actor_id,
        impersonado_id=r.impersonado_id,
        materia_id=r.materia_id,
        accion=r.accion,
        detalle=r.detalle,
        filas_afectadas=r.filas_afectadas,
        ip=r.ip,
    )


@router.get(
    "/panel/acciones-por-dia",
    response_model=AccionesPorDiaResponse,
    dependencies=_GUARD,
)
async def acciones_por_dia(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> AccionesPorDiaResponse:
    svc = AuditoriaPanelService(db, user.tenant_id)
    if desde is None or hasta is None:
        desde, hasta = svc.default_rango()
    try:
        svc.rango_dia(desde, hasta)
        rows = await svc.acciones_por_dia(user, desde=desde, hasta=hasta)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return AccionesPorDiaResponse(
        items=[AccionPorDiaItem(dia=r.dia, accion=r.accion, total=r.total) for r in rows]
    )


@router.get(
    "/panel/comunicaciones-por-docente",
    response_model=ComunicacionesPorDocenteResponse,
    dependencies=_GUARD,
)
async def comunicaciones_por_docente(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComunicacionesPorDocenteResponse:
    svc = AuditoriaPanelService(db, user.tenant_id)
    rows = await svc.comunicaciones_por_docente(user)
    return ComunicacionesPorDocenteResponse(
        items=[
            ComunicacionEstadoItem(
                enviado_por=r.enviado_por, estado=r.estado, total=r.total
            )
            for r in rows
        ]
    )


@router.get(
    "/panel/interacciones",
    response_model=InteraccionesResponse,
    dependencies=_GUARD,
)
async def interacciones(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    desde: datetime | None = None,
    hasta: datetime | None = None,
) -> InteraccionesResponse:
    svc = AuditoriaPanelService(db, user.tenant_id)
    if desde is None or hasta is None:
        desde, hasta = svc.default_rango()
    try:
        svc.rango_dia(desde, hasta)
        rows = await svc.interacciones(user, desde=desde, hasta=hasta)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return InteraccionesResponse(
        items=[
            InteraccionItem(
                actor_id=r.actor_id,
                materia_id=r.materia_id,
                accion=r.accion,
                total=r.total,
            )
            for r in rows
        ]
    )


@router.get("/log", response_model=AuditoriaLogResponse, dependencies=_GUARD)
async def log_completo(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    desde: datetime | None = None,
    hasta: datetime | None = None,
    materia_id: uuid.UUID | None = None,
    usuario_id: uuid.UUID | None = None,
    accion: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=200, ge=1, le=500),
) -> AuditoriaLogResponse:
    svc = AuditoriaPanelService(db, user.tenant_id)
    if desde is not None and hasta is not None:
        try:
            svc.rango_dia(desde, hasta)
        except ValueError as exc:
            raise _http_error(exc) from exc
    rows = await svc.log_completo(
        user,
        desde=desde,
        hasta=hasta,
        materia_id=materia_id,
        usuario_id=usuario_id,
        accion=accion,
        limit=limit,
    )
    return AuditoriaLogResponse(items=[_log_item(r) for r in rows], limit=limit)
