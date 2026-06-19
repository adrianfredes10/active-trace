"""ABM de estructura académica (C-06)."""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.admin_dashboard import ResumenAcademicoResponse
from app.schemas.estructura import (
    CarreraCreate,
    CarreraListResponse,
    CarreraResponse,
    CarreraUpdate,
    CohorteCreate,
    CohorteListResponse,
    CohorteResponse,
    CohorteUpdate,
    MateriaCreate,
    MateriaListResponse,
    MateriaResponse,
    MateriaUpdate,
)
from app.services.admin_dashboard_service import AdminDashboardService
from app.services.estructura_service import EstructuraService

router = APIRouter(
    prefix="/api/admin",
    tags=["estructura"],
    dependencies=[Depends(require_permission("estructura:gestionar"))],
)


def _carrera_response(entity) -> CarreraResponse:
    return CarreraResponse(
        id=entity.id,
        codigo=entity.codigo,
        nombre=entity.nombre,
        estado=entity.estado,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _cohorte_response(entity) -> CohorteResponse:
    return CohorteResponse(
        id=entity.id,
        carrera_id=entity.carrera_id,
        nombre=entity.nombre,
        anio=entity.anio,
        vig_desde=entity.vig_desde,
        vig_hasta=entity.vig_hasta,
        estado=entity.estado,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


def _materia_response(entity) -> MateriaResponse:
    return MateriaResponse(
        id=entity.id,
        codigo=entity.codigo,
        nombre=entity.nombre,
        estado=entity.estado,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get("/resumen-academico", response_model=ResumenAcademicoResponse)
async def resumen_academico(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ResumenAcademicoResponse:
    svc = AdminDashboardService(db, user.tenant_id)
    data = await svc.resumen_academico()
    return ResumenAcademicoResponse(**data)


@router.get("/carreras", response_model=CarreraListResponse)
async def list_carreras(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraListResponse:
    svc = EstructuraService(db, user.tenant_id)
    items = [_carrera_response(c) for c in await svc.list_carreras()]
    return CarreraListResponse(items=items)


@router.post(
    "/carreras",
    response_model=CarreraResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_carrera(
    body: CarreraCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    svc = EstructuraService(db, user.tenant_id)
    carrera = await svc.create_carrera(body)
    await db.commit()
    await db.refresh(carrera)
    return _carrera_response(carrera)


@router.patch("/carreras/{carrera_id}", response_model=CarreraResponse)
async def update_carrera(
    carrera_id: uuid.UUID,
    body: CarreraUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CarreraResponse:
    svc = EstructuraService(db, user.tenant_id)
    carrera = await svc.update_carrera(carrera_id, body)
    await db.commit()
    await db.refresh(carrera)
    return _carrera_response(carrera)


@router.delete("/carreras/{carrera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_carrera(
    carrera_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = EstructuraService(db, user.tenant_id)
    await svc.delete_carrera(carrera_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/cohortes", response_model=CohorteListResponse)
async def list_cohortes(
    carrera_id: uuid.UUID | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteListResponse:
    svc = EstructuraService(db, user.tenant_id)
    items = [_cohorte_response(c) for c in await svc.list_cohortes(carrera_id=carrera_id)]
    return CohorteListResponse(items=items)


@router.post(
    "/cohortes",
    response_model=CohorteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_cohorte(
    body: CohorteCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    svc = EstructuraService(db, user.tenant_id)
    cohorte = await svc.create_cohorte(body)
    await db.commit()
    await db.refresh(cohorte)
    return _cohorte_response(cohorte)


@router.patch("/cohortes/{cohorte_id}", response_model=CohorteResponse)
async def update_cohorte(
    cohorte_id: uuid.UUID,
    body: CohorteUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CohorteResponse:
    svc = EstructuraService(db, user.tenant_id)
    cohorte = await svc.update_cohorte(cohorte_id, body)
    await db.commit()
    await db.refresh(cohorte)
    return _cohorte_response(cohorte)


@router.delete("/cohortes/{cohorte_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cohorte(
    cohorte_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = EstructuraService(db, user.tenant_id)
    await svc.delete_cohorte(cohorte_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/materias", response_model=MateriaListResponse)
async def list_materias(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaListResponse:
    svc = EstructuraService(db, user.tenant_id)
    items = [_materia_response(m) for m in await svc.list_materias()]
    return MateriaListResponse(items=items)


@router.post(
    "/materias",
    response_model=MateriaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_materia(
    body: MateriaCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    svc = EstructuraService(db, user.tenant_id)
    materia = await svc.create_materia(body)
    await db.commit()
    await db.refresh(materia)
    return _materia_response(materia)


@router.patch("/materias/{materia_id}", response_model=MateriaResponse)
async def update_materia(
    materia_id: uuid.UUID,
    body: MateriaUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MateriaResponse:
    svc = EstructuraService(db, user.tenant_id)
    materia = await svc.update_materia(materia_id, body)
    await db.commit()
    await db.refresh(materia)
    return _materia_response(materia)


@router.delete("/materias/{materia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_materia(
    materia_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = EstructuraService(db, user.tenant_id)
    await svc.delete_materia(materia_id)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
