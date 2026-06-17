"""Endpoints de tareas internas — C-16."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.models.tarea import EstadoTarea
from app.schemas.tarea import (
    ComentarioCreate,
    ComentarioListResponse,
    ComentarioResponse,
    TareaCreate,
    TareaDelegar,
    TareaEstadoUpdate,
    TareaListResponse,
    TareaResponse,
)
from app.services.tarea_service import TareaService

router = APIRouter(prefix="/api/tareas", tags=["tareas"])
_GUARD = [Depends(require_permission("tareas:gestionar"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _tarea_response(t: object) -> TareaResponse:
    return TareaResponse(
        id=t.id,
        materia_id=t.materia_id,
        asignado_a=t.asignado_a,
        asignado_por=t.asignado_por,
        estado=t.estado.value if hasattr(t.estado, "value") else str(t.estado),
        descripcion=t.descripcion,
        contexto_id=t.contexto_id,
    )


@router.post(
    "",
    response_model=TareaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GUARD,
)
async def crear_tarea(
    body: TareaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponse:
    svc = TareaService(db, user.tenant_id)
    try:
        tarea = await svc.crear(
            user=user,
            asignado_a=body.asignado_a,
            descripcion=body.descripcion,
            materia_id=body.materia_id,
            contexto_id=body.contexto_id,
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return _tarea_response(tarea)


@router.get("/mias", response_model=TareaListResponse, dependencies=_GUARD)
async def mis_tareas(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaListResponse:
    svc = TareaService(db, user.tenant_id)
    items = await svc.listar_mias(user)
    return TareaListResponse(items=[_tarea_response(t) for t in items])


@router.get("/admin", response_model=TareaListResponse, dependencies=_GUARD)
async def admin_tareas(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    asignado_a: uuid.UUID | None = None,
    asignado_por: uuid.UUID | None = None,
    materia_id: uuid.UUID | None = None,
    estado: EstadoTarea | None = None,
    busqueda: str | None = Query(default=None, max_length=200),
) -> TareaListResponse:
    svc = TareaService(db, user.tenant_id)
    try:
        items = await svc.listar_admin(
            user,
            asignado_a=asignado_a,
            asignado_por=asignado_por,
            materia_id=materia_id,
            estado=estado,
            busqueda=busqueda,
        )
    except PermissionError as exc:
        raise _http_error(exc) from exc
    return TareaListResponse(items=[_tarea_response(t) for t in items])


@router.patch("/{tarea_id}/estado", response_model=TareaResponse, dependencies=_GUARD)
async def actualizar_estado(
    tarea_id: uuid.UUID,
    body: TareaEstadoUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponse:
    svc = TareaService(db, user.tenant_id)
    try:
        tarea = await svc.cambiar_estado(tarea_id, user=user, estado=body.estado)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return _tarea_response(tarea)


@router.post("/{tarea_id}/delegar", response_model=TareaResponse, dependencies=_GUARD)
async def delegar_tarea(
    tarea_id: uuid.UUID,
    body: TareaDelegar,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TareaResponse:
    svc = TareaService(db, user.tenant_id)
    try:
        tarea = await svc.delegar(
            tarea_id, user=user, nuevo_asignado=body.asignado_a
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return _tarea_response(tarea)


@router.post(
    "/{tarea_id}/comentarios",
    response_model=ComentarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GUARD,
)
async def agregar_comentario(
    tarea_id: uuid.UUID,
    body: ComentarioCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComentarioResponse:
    svc = TareaService(db, user.tenant_id)
    try:
        c = await svc.agregar_comentario(tarea_id, user=user, texto=body.texto)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return ComentarioResponse(
        id=c.id,
        tarea_id=c.tarea_id,
        autor_id=c.autor_id,
        texto=c.texto,
        creado_at=c.creado_at,
    )


@router.get(
    "/{tarea_id}/comentarios",
    response_model=ComentarioListResponse,
    dependencies=_GUARD,
)
async def listar_comentarios(
    tarea_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ComentarioListResponse:
    svc = TareaService(db, user.tenant_id)
    try:
        items = await svc.listar_comentarios(tarea_id, user)
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return ComentarioListResponse(
        items=[
            ComentarioResponse(
                id=c.id,
                tarea_id=c.tarea_id,
                autor_id=c.autor_id,
                texto=c.texto,
                creado_at=c.creado_at,
            )
            for c in items
        ]
    )
