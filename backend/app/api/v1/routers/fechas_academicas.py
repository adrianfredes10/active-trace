"""Endpoints de fechas académicas — C-17."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.models.evaluacion import TipoEvaluacion
from app.schemas.programa_academico import (
    FechaAcademicaCreate,
    FechaAcademicaListResponse,
    FechaAcademicaResponse,
    FechaAcademicaUpdate,
    HtmlFechasResponse,
)
from app.services.programa_academico_service import FechaAcademicaService

router = APIRouter(prefix="/api/fechas-academicas", tags=["fechas-academicas"])
_GUARD = [Depends(require_permission("estructura:gestionar"))]


def _http_error(exc: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _fecha_response(f: object) -> FechaAcademicaResponse:
    return FechaAcademicaResponse(
        id=f.id,
        materia_id=f.materia_id,
        cohorte_id=f.cohorte_id,
        tipo=f.tipo.value if hasattr(f.tipo, "value") else str(f.tipo),
        numero=f.numero,
        periodo=f.periodo,
        fecha=f.fecha,
        titulo=f.titulo,
    )


@router.post(
    "",
    response_model=FechaAcademicaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GUARD,
)
async def crear_fecha(
    body: FechaAcademicaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FechaAcademicaResponse:
    svc = FechaAcademicaService(db, user.tenant_id)
    try:
        entity = await svc.crear(
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            tipo=body.tipo,
            numero=body.numero,
            periodo=body.periodo,
            fecha=body.fecha,
            titulo=body.titulo,
        )
        await db.commit()
    except ValueError as exc:
        raise _http_error(exc) from exc
    return _fecha_response(entity)


@router.get("", response_model=FechaAcademicaListResponse, dependencies=_GUARD)
async def listar_fechas(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    tipo: TipoEvaluacion | None = None,
    periodo: str | None = Query(default=None, max_length=20),
) -> FechaAcademicaListResponse:
    svc = FechaAcademicaService(db, user.tenant_id)
    items = await svc.listar(
        materia_id=materia_id, cohorte_id=cohorte_id, tipo=tipo, periodo=periodo
    )
    return FechaAcademicaListResponse(items=[_fecha_response(f) for f in items])


@router.get("/calendario", response_model=FechaAcademicaListResponse, dependencies=_GUARD)
async def calendario_fechas(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    desde: date,
    hasta: date,
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
) -> FechaAcademicaListResponse:
    svc = FechaAcademicaService(db, user.tenant_id)
    try:
        items = await svc.calendario(
            desde=desde, hasta=hasta, materia_id=materia_id, cohorte_id=cohorte_id
        )
    except ValueError as exc:
        raise _http_error(exc) from exc
    return FechaAcademicaListResponse(items=[_fecha_response(f) for f in items])


@router.patch("/{fecha_id}", response_model=FechaAcademicaResponse, dependencies=_GUARD)
async def actualizar_fecha(
    fecha_id: uuid.UUID,
    body: FechaAcademicaUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FechaAcademicaResponse:
    svc = FechaAcademicaService(db, user.tenant_id)
    try:
        entity = await svc.actualizar(
            fecha_id,
            tipo=body.tipo,
            numero=body.numero,
            periodo=body.periodo,
            fecha=body.fecha,
            titulo=body.titulo,
        )
        await db.commit()
    except ValueError as exc:
        raise _http_error(exc) from exc
    return _fecha_response(entity)


@router.delete("/{fecha_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_GUARD)
async def eliminar_fecha(
    fecha_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = FechaAcademicaService(db, user.tenant_id)
    try:
        await svc.eliminar(fecha_id)
        await db.commit()
    except ValueError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/html/{materia_id}",
    response_model=HtmlFechasResponse,
    dependencies=_GUARD,
)
async def html_aula_fechas(
    materia_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    cohorte_id: uuid.UUID,
) -> HtmlFechasResponse:
    svc = FechaAcademicaService(db, user.tenant_id)
    try:
        html = await svc.html_aula(materia_id=materia_id, cohorte_id=cohorte_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return HtmlFechasResponse(html=html)
