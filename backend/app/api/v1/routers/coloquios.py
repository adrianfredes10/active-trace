"""Endpoints de coloquios — C-14."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.repositories.evaluacion_repository import ReservaEvaluacionRepository
from app.schemas.coloquio import (
    ConvocatoriaCreate,
    ConvocatoriaListResponse,
    ConvocatoriaMetricasResponse,
    ConvocatoriaResponse,
    ConvocadosImport,
    MetricasGlobalesResponse,
    ReservaCreate,
    ReservaListResponse,
    ReservaResponse,
    ResultadoCreate,
    ResultadoListResponse,
    ResultadoResponse,
    TurnoResponse,
)
from app.services.coloquio_service import ColoquioService, TurnoInput

router = APIRouter(prefix="/api/coloquios", tags=["coloquios"])
_GESTION = [Depends(require_permission("evaluaciones:gestionar"))]
_RESERVAR = [Depends(require_permission("evaluaciones:reservar"))]


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


def _metricas_response(m: object) -> ConvocatoriaMetricasResponse:
    return ConvocatoriaMetricasResponse(
        evaluacion_id=m.evaluacion_id,
        materia_id=m.materia_id,
        cohorte_id=m.cohorte_id,
        instancia=m.instancia,
        tipo=m.tipo,
        estado=m.estado,
        convocados=m.convocados,
        reservas_activas=m.reservas_activas,
        cupos_libres=m.cupos_libres,
        notas_registradas=m.notas_registradas,
    )


@router.post(
    "/convocatorias",
    response_model=ConvocatoriaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GESTION,
)
async def crear_convocatoria(
    body: ConvocatoriaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConvocatoriaResponse:
    svc = ColoquioService(db, user.tenant_id)
    try:
        evaluacion, turnos = await svc.crear_convocatoria(
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            instancia=body.instancia,
            tipo=body.tipo,
            dias_disponibles=body.dias_disponibles,
            turnos=[
                TurnoInput(fecha=t.fecha, hora=t.hora, cupo_max=t.cupo_max)
                for t in body.turnos
            ],
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc

    reservas_repo = ReservaEvaluacionRepository(db, user.tenant_id)
    turnos_resp: list[TurnoResponse] = []
    for turno in turnos:
        activas = await reservas_repo.count_activas_por_turno(turno.id)
        turnos_resp.append(
            TurnoResponse(
                id=turno.id,
                fecha=turno.fecha,
                hora=turno.hora,
                cupo_max=turno.cupo_max,
                reservas_activas=activas,
                cupos_libres=max(0, turno.cupo_max - activas),
            )
        )
    return ConvocatoriaResponse(
        id=evaluacion.id,
        materia_id=evaluacion.materia_id,
        cohorte_id=evaluacion.cohorte_id,
        instancia=evaluacion.instancia,
        tipo=evaluacion.tipo.value,
        estado=evaluacion.estado.value,
        dias_disponibles=evaluacion.dias_disponibles,
        turnos=turnos_resp,
    )


@router.post(
    "/convocatorias/{evaluacion_id}/convocados",
    status_code=status.HTTP_200_OK,
    dependencies=_GESTION,
)
async def importar_convocados(
    evaluacion_id: uuid.UUID,
    body: ConvocadosImport,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, int]:
    svc = ColoquioService(db, user.tenant_id)
    try:
        count = await svc.importar_convocados(evaluacion_id, body.alumno_ids)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return {"importados": count}


@router.get(
    "/convocatorias",
    response_model=ConvocatoriaListResponse,
    dependencies=_GESTION,
)
async def listar_convocatorias(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConvocatoriaListResponse:
    svc = ColoquioService(db, user.tenant_id)
    items = await svc.listar_convocatorias()
    return ConvocatoriaListResponse(items=[_metricas_response(m) for m in items])


@router.get(
    "/convocatorias/{evaluacion_id}",
    response_model=ConvocatoriaMetricasResponse,
    dependencies=_GESTION,
)
async def detalle_convocatoria(
    evaluacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConvocatoriaMetricasResponse:
    svc = ColoquioService(db, user.tenant_id)
    try:
        metricas = await svc.metricas_convocatoria(evaluacion_id)
    except ValueError as exc:
        raise _http_error(exc) from exc
    return _metricas_response(metricas)


@router.get(
    "/metricas",
    response_model=MetricasGlobalesResponse,
    dependencies=_GESTION,
)
async def metricas_globales(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MetricasGlobalesResponse:
    svc = ColoquioService(db, user.tenant_id)
    m = await svc.metricas_globales()
    return MetricasGlobalesResponse(
        convocados_total=m.convocados_total,
        instancias_activas=m.instancias_activas,
        reservas_activas=m.reservas_activas,
        notas_registradas=m.notas_registradas,
    )


@router.post(
    "/convocatorias/{evaluacion_id}/reservas",
    response_model=ReservaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_RESERVAR,
)
async def reservar_turno(
    evaluacion_id: uuid.UUID,
    body: ReservaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservaResponse:
    svc = ColoquioService(db, user.tenant_id)
    try:
        reserva = await svc.reservar_turno(
            user=user, evaluacion_id=evaluacion_id, turno_id=body.turno_id
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return ReservaResponse(
        id=reserva.id,
        evaluacion_id=reserva.evaluacion_id,
        turno_id=reserva.turno_id,
        alumno_id=reserva.alumno_id,
        fecha_hora=reserva.fecha_hora,
        estado=reserva.estado.value,
    )


@router.patch(
    "/reservas/{reserva_id}/cancelar",
    response_model=ReservaResponse,
    dependencies=_RESERVAR,
)
async def cancelar_reserva(
    reserva_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservaResponse:
    svc = ColoquioService(db, user.tenant_id)
    try:
        reserva = await svc.cancelar_reserva(reserva_id, user)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return ReservaResponse(
        id=reserva.id,
        evaluacion_id=reserva.evaluacion_id,
        turno_id=reserva.turno_id,
        alumno_id=reserva.alumno_id,
        fecha_hora=reserva.fecha_hora,
        estado=reserva.estado.value,
    )


@router.get(
    "/admin/agenda",
    response_model=ReservaListResponse,
    dependencies=_GESTION,
)
async def agenda_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReservaListResponse:
    svc = ColoquioService(db, user.tenant_id)
    reservas = await svc.agenda_activa()
    return ReservaListResponse(
        items=[
            ReservaResponse(
                id=r.id,
                evaluacion_id=r.evaluacion_id,
                turno_id=r.turno_id,
                alumno_id=r.alumno_id,
                fecha_hora=r.fecha_hora,
                estado=r.estado.value,
            )
            for r in reservas
        ]
    )


@router.post(
    "/convocatorias/{evaluacion_id}/resultados",
    response_model=ResultadoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GESTION,
)
async def registrar_resultado(
    evaluacion_id: uuid.UUID,
    body: ResultadoCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResultadoResponse:
    svc = ColoquioService(db, user.tenant_id)
    try:
        resultado = await svc.registrar_resultado(
            evaluacion_id, alumno_id=body.alumno_id, nota_final=body.nota_final
        )
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return ResultadoResponse(
        id=resultado.id,
        evaluacion_id=resultado.evaluacion_id,
        alumno_id=resultado.alumno_id,
        nota_final=resultado.nota_final,
    )


@router.get(
    "/resultados",
    response_model=ResultadoListResponse,
    dependencies=_GESTION,
)
async def listar_resultados(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResultadoListResponse:
    svc = ColoquioService(db, user.tenant_id)
    resultados = await svc.listar_resultados()
    return ResultadoListResponse(
        items=[
            ResultadoResponse(
                id=r.id,
                evaluacion_id=r.evaluacion_id,
                alumno_id=r.alumno_id,
                nota_final=r.nota_final,
            )
            for r in resultados
        ]
    )


@router.patch(
    "/convocatorias/{evaluacion_id}/cerrar",
    response_model=ConvocatoriaMetricasResponse,
    dependencies=_GESTION,
)
async def cerrar_convocatoria(
    evaluacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConvocatoriaMetricasResponse:
    svc = ColoquioService(db, user.tenant_id)
    try:
        await svc.cerrar_convocatoria(evaluacion_id)
        metricas = await svc.metricas_convocatoria(evaluacion_id)
        await db.commit()
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return _metricas_response(metricas)
