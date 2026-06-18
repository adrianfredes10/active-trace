"""Endpoints de calificaciones — C-10."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.calificacion import (
    ActividadDetectadaResponse,
    CalificacionImportResponse,
    CalificacionPreviewResponse,
    CalificacionResponse,
    EntregaSinCorregirResponse,
    FinalizacionPreviewRequest,
    UmbralMateriaResponse,
    UmbralMateriaUpdate,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.calificacion_service import CalificacionService
from app.services.padron_parser import PadronParseError

router = APIRouter(
    prefix="/api/calificaciones",
    tags=["calificaciones"],
)


def _calificacion_response(c: object) -> CalificacionResponse:
    return CalificacionResponse(
        id=c.id,
        entrada_padron_id=c.entrada_padron_id,
        actividad=c.actividad,
        nota_numerica=c.nota_numerica,
        nota_textual=c.nota_textual,
        aprobado=c.aprobado,
        origen=c.origen.value if hasattr(c.origen, "value") else str(c.origen),
        importado_at=c.importado_at,
    )


@router.post(
    "/preview",
    response_model=CalificacionPreviewResponse,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def preview_calificaciones(file: UploadFile = File(...)) -> CalificacionPreviewResponse:
    content = await file.read()
    try:
        from app.services.calificacion_parser import preview_calificaciones_csv

        preview = preview_calificaciones_csv(content)
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return CalificacionPreviewResponse(
        actividades=[
            ActividadDetectadaResponse(nombre=a.nombre, tipo=a.tipo)
            for a in preview.actividades
        ],
        total_filas=len(preview.filas),
        muestra_emails=[f.email for f in preview.filas[:5]],
    )


@router.post(
    "/importar",
    response_model=CalificacionImportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def importar_calificaciones(
    request: Request,
    asignacion_id: Annotated[uuid.UUID, Form(...)],
    materia_id: Annotated[uuid.UUID, Form(...)],
    cohorte_id: Annotated[uuid.UUID, Form(...)],
    actividades: Annotated[str, Form(...)],
    comision: Annotated[str | None, Form()] = None,
    file: UploadFile = File(...),
    user: Annotated[CurrentUser, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> CalificacionImportResponse:
    actividades_list = [a.strip() for a in actividades.split(",") if a.strip()]
    if not actividades_list:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe seleccionar al menos una actividad",
        )
    content = await file.read()
    svc = CalificacionService(db, user.tenant_id)
    try:
        items = await svc.importar_calificaciones(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            actividades_seleccionadas=actividades_list,
            content=content,
            user=user,
            comision_activa=comision,
        )
    except (PadronParseError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.CALIFICACIONES_IMPORTAR,
        detalle={
            "asignacion_id": str(asignacion_id),
            "actividades": actividades_list,
            "importadas": len(items),
        },
        materia_id=materia_id,
        filas_afectadas=len(items),
    )
    await db.commit()
    return CalificacionImportResponse(
        importadas=len(items),
        items=[_calificacion_response(c) for c in items],
    )


@router.put(
    "/umbral",
    response_model=UmbralMateriaResponse,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def configurar_umbral(
    body: UmbralMateriaUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UmbralMateriaResponse:
    svc = CalificacionService(db, user.tenant_id)
    umbral = await svc.configurar_umbral(
        asignacion_id=body.asignacion_id,
        materia_id=body.materia_id,
        umbral_pct=body.umbral_pct,
        valores_aprobatorios=body.valores_aprobatorios,
    )
    await svc.recalcular_aprobado_asignacion(body.asignacion_id)
    await db.commit()
    await db.refresh(umbral)
    return UmbralMateriaResponse(
        id=umbral.id,
        asignacion_id=umbral.asignacion_id,
        materia_id=umbral.materia_id,
        umbral_pct=umbral.umbral_pct,
        valores_aprobatorios=list(umbral.valores_aprobatorios or []),
    )


@router.get(
    "/umbral/{asignacion_id}",
    response_model=UmbralMateriaResponse,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def obtener_umbral(
    asignacion_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UmbralMateriaResponse:
    svc = CalificacionService(db, user.tenant_id)
    umbral = await svc.get_umbral(asignacion_id)
    if umbral is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No configurado")
    return UmbralMateriaResponse(
        id=umbral.id,
        asignacion_id=umbral.asignacion_id,
        materia_id=umbral.materia_id,
        umbral_pct=umbral.umbral_pct,
        valores_aprobatorios=list(umbral.valores_aprobatorios or []),
    )


@router.post(
    "/finalizacion/preview",
    response_model=EntregaSinCorregirResponse,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def preview_finalizacion(
    asignacion_id: Annotated[uuid.UUID, Form(...)],
    materia_id: Annotated[uuid.UUID, Form(...)],
    cohorte_id: Annotated[uuid.UUID, Form(...)],
    comision: Annotated[str | None, Form()] = None,
    file: UploadFile = File(...),
    user: Annotated[CurrentUser, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> EntregaSinCorregirResponse:
    content = await file.read()
    svc = CalificacionService(db, user.tenant_id)
    try:
        items = await svc.detectar_entregas_sin_corregir(
            asignacion_id=asignacion_id,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            content=content,
            user=user,
            comision_activa=comision,
        )
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return EntregaSinCorregirResponse(items=items)
