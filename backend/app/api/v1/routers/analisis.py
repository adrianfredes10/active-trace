"""Endpoints de análisis académico — C-11."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.analisis import (
    AgrupacionesUpdate,
    AgrupacionNotaFinal,
    AtrasadosResponse,
    AlumnoAtrasadoResponse,
    MonitorAlumnoResponse,
    MonitorResponse,
    NotaFinalAlumnoResponse,
    NotasFinalesResponse,
    RankingItemResponse,
    RankingResponse,
    ReporteRapidoResponse,
    SinCorregirItemResponse,
    SinCorregirResponse,
)
from app.services.analisis_service import AnalisisService

router = APIRouter(prefix="/api/analisis", tags=["analisis"])

_GUARD = [Depends(require_permission("atrasados:ver"))]


def _svc(db: AsyncSession, user: CurrentUser) -> AnalisisService:
    return AnalisisService(db, user.tenant_id)


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


@router.get("/atrasados", response_model=AtrasadosResponse, dependencies=_GUARD)
async def atrasados(
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AtrasadosResponse:
    try:
        data = await _svc(db, user).listar_atrasados(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return AtrasadosResponse(
        total_alumnos=data["total_alumnos"],
        total_atrasados=data["total_atrasados"],
        items=[AlumnoAtrasadoResponse(**i) for i in data["items"]],
    )


@router.get("/ranking", response_model=RankingResponse, dependencies=_GUARD)
async def ranking(
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RankingResponse:
    try:
        items = await _svc(db, user).ranking(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return RankingResponse(items=[RankingItemResponse(**i) for i in items])


@router.get("/reporte-rapido", response_model=ReporteRapidoResponse, dependencies=_GUARD)
async def reporte_rapido(
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReporteRapidoResponse:
    try:
        data = await _svc(db, user).reporte_rapido(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return ReporteRapidoResponse(**data)


@router.put("/agrupaciones", dependencies=_GUARD)
async def configurar_agrupaciones(
    body: AgrupacionesUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AgrupacionNotaFinal]:
    try:
        agrupaciones = await _svc(db, user).configurar_agrupaciones(
            asignacion_id=body.asignacion_id,
            materia_id=body.materia_id,
            agrupaciones=[g.model_dump() for g in body.agrupaciones],
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return [AgrupacionNotaFinal(**g) for g in agrupaciones]


@router.get("/notas-finales", response_model=NotasFinalesResponse, dependencies=_GUARD)
async def notas_finales(
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NotasFinalesResponse:
    try:
        data = await _svc(db, user).notas_finales(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return NotasFinalesResponse(
        agrupaciones=[AgrupacionNotaFinal(**g) for g in data["agrupaciones"]],
        items=[NotaFinalAlumnoResponse(**i) for i in data["items"]],
    )


@router.get("/sin-corregir", response_model=SinCorregirResponse, dependencies=_GUARD)
async def sin_corregir(
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SinCorregirResponse:
    try:
        items = await _svc(db, user).sin_corregir(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return SinCorregirResponse(
        items=[SinCorregirItemResponse(**i) for i in items]
    )


@router.get("/sin-corregir/export", dependencies=_GUARD)
async def exportar_sin_corregir(
    asignacion_id: uuid.UUID,
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    svc = _svc(db, user)
    try:
        items = await svc.sin_corregir(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            user=user,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    content = svc.exportar_sin_corregir_csv(items)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="sin_corregir.csv"'},
    )


@router.get("/monitor/seguimiento", response_model=MonitorResponse, dependencies=_GUARD)
async def monitor_seguimiento(
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    asignacion_id: uuid.UUID,
    comision: str | None = None,
    regional: str | None = None,
    email: str | None = None,
    actividad: str | None = None,
    min_aprobadas: int | None = Query(default=None, ge=0),
    solo_atrasados: bool = False,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MonitorResponse:
    filtros = {
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "asignacion_id": asignacion_id,
        "comision": comision,
        "regional": regional,
        "email": email,
        "actividad": actividad,
        "min_aprobadas": min_aprobadas,
        "solo_atrasados": solo_atrasados,
    }
    try:
        items = await _svc(db, user).monitor(
            filtros=filtros, user=user, requiere_asignacion_propia=True
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return MonitorResponse(items=[MonitorAlumnoResponse(**i) for i in items])


@router.get("/monitor/general", response_model=MonitorResponse, dependencies=_GUARD)
async def monitor_general(
    materia_id: uuid.UUID,
    cohorte_id: uuid.UUID,
    asignacion_id: uuid.UUID | None = None,
    comision: str | None = None,
    regional: str | None = None,
    email: str | None = None,
    actividad: str | None = None,
    min_aprobadas: int | None = Query(default=None, ge=0),
    solo_atrasados: bool = False,
    importado_desde: Annotated[str | None, Query()] = None,
    importado_hasta: Annotated[str | None, Query()] = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MonitorResponse:
    from datetime import datetime

    filtros = {
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "asignacion_id": asignacion_id,
        "comision": comision,
        "regional": regional,
        "email": email,
        "actividad": actividad,
        "min_aprobadas": min_aprobadas,
        "solo_atrasados": solo_atrasados,
        "importado_desde": (
            datetime.fromisoformat(importado_desde) if importado_desde else None
        ),
        "importado_hasta": (
            datetime.fromisoformat(importado_hasta) if importado_hasta else None
        ),
    }
    try:
        items = await _svc(db, user).monitor(
            filtros=filtros, user=user, requiere_asignacion_propia=False
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return MonitorResponse(items=[MonitorAlumnoResponse(**i) for i in items])
