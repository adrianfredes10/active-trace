"""Endpoints de programas de materia — C-17."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.programa_academico import (
    ProgramaCreate,
    ProgramaListResponse,
    ProgramaResponse,
)
from app.services.programa_academico_service import ProgramaService

router = APIRouter(prefix="/api/programas", tags=["programas"])
_GUARD = [Depends(require_permission("estructura:gestionar"))]


def _http_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _programa_response(p: object) -> ProgramaResponse:
    return ProgramaResponse(
        id=p.id,
        materia_id=p.materia_id,
        carrera_id=p.carrera_id,
        cohorte_id=p.cohorte_id,
        titulo=p.titulo,
        referencia_archivo=p.referencia_archivo,
        cargado_at=p.cargado_at,
    )


@router.post(
    "",
    response_model=ProgramaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GUARD,
)
async def asociar_programa(
    body: ProgramaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaResponse:
    svc = ProgramaService(db, user.tenant_id)
    try:
        programa = await svc.asociar(
            materia_id=body.materia_id,
            carrera_id=body.carrera_id,
            cohorte_id=body.cohorte_id,
            titulo=body.titulo,
            nombre_archivo=body.nombre_archivo,
        )
        await db.commit()
    except ValueError as exc:
        raise _http_error(exc) from exc
    return _programa_response(programa)


@router.get("", response_model=ProgramaListResponse, dependencies=_GUARD)
async def listar_programas(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: uuid.UUID | None = None,
    carrera_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
) -> ProgramaListResponse:
    svc = ProgramaService(db, user.tenant_id)
    items = await svc.listar(
        materia_id=materia_id, carrera_id=carrera_id, cohorte_id=cohorte_id
    )
    return ProgramaListResponse(items=[_programa_response(p) for p in items])


@router.get("/{programa_id}", response_model=ProgramaResponse, dependencies=_GUARD)
async def obtener_programa(
    programa_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProgramaResponse:
    svc = ProgramaService(db, user.tenant_id)
    try:
        programa = await svc.obtener(programa_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return _programa_response(programa)


@router.delete("/{programa_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_GUARD)
async def eliminar_programa(
    programa_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = ProgramaService(db, user.tenant_id)
    try:
        await svc.eliminar(programa_id)
        await db.commit()
    except ValueError as exc:
        raise _http_error(exc) from exc
