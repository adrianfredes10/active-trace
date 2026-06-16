"""Endpoints de equipos docentes — C-08 (F4.2–F4.7)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.asignacion import asignacion_response
from app.schemas.equipos import (
    AsignacionMasivaRequest,
    ClonarEquipoRequest,
    EquipoListResponse,
    ModificarVigenciaEquipoRequest,
    OperacionEquipoResponse,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.equipos_service import EquiposService

router = APIRouter(prefix="/api/equipos", tags=["equipos"])


async def _audit_equipo(
    db: AsyncSession,
    user: CurrentUser,
    request: Request,
    *,
    accion: AuditAction,
    detalle: dict,
    materia_id: uuid.UUID | None = None,
    filas: int = 0,
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
        filas_afectadas=filas,
    )


@router.get("/mis-equipos", response_model=EquipoListResponse)
async def mis_equipos(
    solo_vigentes: bool = Query(default=True),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EquipoListResponse:
    """F4.2 — asignaciones del usuario autenticado (identidad desde sesión)."""
    svc = EquiposService(db, user.tenant_id)
    items = await svc.mis_equipos(user.id, solo_vigentes=solo_vigentes)
    return EquipoListResponse(items=[asignacion_response(a) for a in items])


@router.post(
    "/asignacion-masiva",
    response_model=OperacionEquipoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("equipos:asignar"))],
)
async def asignacion_masiva(
    body: AsignacionMasivaRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OperacionEquipoResponse:
    """F4.4 — asignación masiva de docentes."""
    svc = EquiposService(db, user.tenant_id)
    try:
        creadas = await svc.asignacion_masiva(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    await _audit_equipo(
        db,
        user,
        request,
        accion=AuditAction.ASIGNACION_MODIFICAR,
        detalle={
            "operacion": "asignacion_masiva",
            "materia_id": str(body.materia_id),
            "cohorte_id": str(body.cohorte_id),
        },
        materia_id=body.materia_id,
        filas=len(creadas),
    )
    await db.commit()
    return OperacionEquipoResponse(
        creadas=len(creadas),
        items=[asignacion_response(a) for a in creadas],
    )


@router.post(
    "/clonar",
    response_model=OperacionEquipoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("equipos:asignar"))],
)
async def clonar_equipo(
    body: ClonarEquipoRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OperacionEquipoResponse:
    """F4.5 / RN-12 — clonar equipo entre cohortes."""
    svc = EquiposService(db, user.tenant_id)
    try:
        clonadas = await svc.clonar_equipo(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    await _audit_equipo(
        db,
        user,
        request,
        accion=AuditAction.ASIGNACION_MODIFICAR,
        detalle={
            "operacion": "clonar_equipo",
            "origen_cohorte_id": str(body.origen.cohorte_id),
            "destino_cohorte_id": str(body.destino.cohorte_id),
        },
        materia_id=body.destino.materia_id,
        filas=len(clonadas),
    )
    await db.commit()
    return OperacionEquipoResponse(
        creadas=len(clonadas),
        items=[asignacion_response(a) for a in clonadas],
    )


@router.patch(
    "/vigencia",
    response_model=OperacionEquipoResponse,
    dependencies=[Depends(require_permission("equipos:asignar"))],
)
async def modificar_vigencia_equipo(
    body: ModificarVigenciaEquipoRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OperacionEquipoResponse:
    """F4.6 — modificar vigencia de todo el equipo en bloque."""
    svc = EquiposService(db, user.tenant_id)
    try:
        actualizadas = await svc.modificar_vigencia_equipo(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    await _audit_equipo(
        db,
        user,
        request,
        accion=AuditAction.ASIGNACION_MODIFICAR,
        detalle={
            "operacion": "modificar_vigencia_equipo",
            "cohorte_id": str(body.cohorte_id),
            "desde": body.desde.isoformat(),
            "hasta": body.hasta.isoformat() if body.hasta else None,
        },
        materia_id=body.materia_id,
        filas=len(actualizadas),
    )
    await db.commit()
    return OperacionEquipoResponse(
        actualizadas=len(actualizadas),
        items=[asignacion_response(a) for a in actualizadas],
    )


@router.get(
    "/exportar",
    dependencies=[Depends(require_permission("equipos:asignar"))],
)
async def exportar_equipo(
    materia_id: uuid.UUID,
    carrera_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """F4.7 — exportar equipo docente a CSV."""
    svc = EquiposService(db, user.tenant_id)
    csv_content = await svc.exportar_equipo_csv(
        materia_id=materia_id,
        carrera_id=carrera_id,
        cohorte_id=cohorte_id,
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=equipo_docente.csv"},
    )
