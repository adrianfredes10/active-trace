"""Endpoints de avisos — C-15."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.aviso import (
    AckResponse,
    AvisoCreate,
    AvisoListResponse,
    AvisoMetricasResponse,
    AvisoResponse,
    AvisoUpdate,
)
from app.services.aviso_service import AvisoService

router = APIRouter(prefix="/api/avisos", tags=["avisos"])
_PUBLICAR = [Depends(require_permission("avisos:publicar"))]
_CONFIRMAR = [Depends(require_permission("avisos:confirmar"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _aviso_response(a: object) -> AvisoResponse:
    return AvisoResponse(
        id=a.id,
        alcance=a.alcance.value if hasattr(a.alcance, "value") else str(a.alcance),
        materia_id=a.materia_id,
        cohorte_id=a.cohorte_id,
        rol_destino=a.rol_destino,
        severidad=a.severidad.value if hasattr(a.severidad, "value") else str(a.severidad),
        titulo=a.titulo,
        cuerpo=a.cuerpo,
        inicio_en=a.inicio_en,
        fin_en=a.fin_en,
        orden=a.orden,
        activo=a.activo,
        requiere_ack=a.requiere_ack,
    )


@router.post(
    "",
    response_model=AvisoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_PUBLICAR,
)
async def crear_aviso(
    body: AvisoCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponse:
    svc = AvisoService(db, user.tenant_id)
    try:
        aviso = await svc.crear(
            alcance=body.alcance,
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            rol_destino=body.rol_destino,
            severidad=body.severidad,
            titulo=body.titulo,
            cuerpo=body.cuerpo,
            inicio_en=body.inicio_en,
            fin_en=body.fin_en,
            orden=body.orden,
            requiere_ack=body.requiere_ack,
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return _aviso_response(aviso)


@router.get("", response_model=AvisoListResponse, dependencies=_PUBLICAR)
async def listar_gestion(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoListResponse:
    svc = AvisoService(db, user.tenant_id)
    items = await svc.listar_gestion()
    return AvisoListResponse(items=[_aviso_response(a) for a in items])


@router.get("/mios", response_model=AvisoListResponse, dependencies=_CONFIRMAR)
async def listar_mios(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoListResponse:
    svc = AvisoService(db, user.tenant_id)
    items = await svc.listar_para_usuario(user)
    return AvisoListResponse(items=[_aviso_response(a) for a in items])


@router.patch("/{aviso_id}", response_model=AvisoResponse, dependencies=_PUBLICAR)
async def actualizar_aviso(
    aviso_id: uuid.UUID,
    body: AvisoUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoResponse:
    svc = AvisoService(db, user.tenant_id)
    try:
        aviso = await svc.actualizar(
            aviso_id,
            titulo=body.titulo,
            cuerpo=body.cuerpo,
            inicio_en=body.inicio_en,
            fin_en=body.fin_en,
            orden=body.orden,
            activo=body.activo,
            requiere_ack=body.requiere_ack,
            severidad=body.severidad,
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return _aviso_response(aviso)


@router.delete("/{aviso_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_PUBLICAR)
async def eliminar_aviso(
    aviso_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = AvisoService(db, user.tenant_id)
    try:
        await svc.eliminar(aviso_id)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc


@router.post(
    "/{aviso_id}/ack",
    response_model=AckResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_CONFIRMAR,
)
async def confirmar_aviso(
    aviso_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AckResponse:
    svc = AvisoService(db, user.tenant_id)
    try:
        ack = await svc.confirmar(aviso_id, user)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return AckResponse(
        aviso_id=ack.aviso_id,
        usuario_id=ack.usuario_id,
        confirmado_at=ack.confirmado_at,
    )


@router.get(
    "/{aviso_id}/metricas",
    response_model=AvisoMetricasResponse,
    dependencies=_PUBLICAR,
)
async def metricas_aviso(
    aviso_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AvisoMetricasResponse:
    svc = AvisoService(db, user.tenant_id)
    try:
        m = await svc.metricas(aviso_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return AvisoMetricasResponse(aviso_id=m.aviso_id, confirmaciones=m.confirmaciones)
