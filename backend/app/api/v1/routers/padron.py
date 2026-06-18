"""Endpoints de padrón — C-09 (F1.3–F1.5)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.config import Settings, get_settings
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.integrations.moodle_ws import MoodleUnavailable, MoodleWSClient
from app.repositories.padron_repository import EntradaPadronRepository
from app.schemas.padron import (
    ActualizarComisionRequest,
    EntradaPadronResponse,
    FilaPadronPreview,
    MoodleSyncRequest,
    PadronImportResponse,
    PadronPreviewResponse,
    VaciarPadronResponse,
    VersionPadronResponse,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.padron_parser import PadronParseError, parse_padron_file
from app.services.padron_service import PadronService

router = APIRouter(prefix="/api/padron", tags=["padron"])


def _version_response(version, total: int) -> VersionPadronResponse:
    return VersionPadronResponse(
        id=version.id,
        materia_id=version.materia_id,
        cohorte_id=version.cohorte_id,
        cargado_por=version.cargado_por,
        cargado_at=version.cargado_at,
        activa=version.activa,
        total_entradas=total,
    )


def _entrada_response(entrada) -> EntradaPadronResponse:
    return EntradaPadronResponse(
        id=entrada.id,
        nombre=entrada.nombre,
        apellidos=entrada.apellidos,
        comision=entrada.comision,
        regional=entrada.regional,
        usuario_id=entrada.usuario_id,
    )


@router.post(
    "/preview",
    response_model=PadronPreviewResponse,
    dependencies=[Depends(require_permission("padron:importar"))],
)
async def preview_padron(
    file: UploadFile = File(...),
) -> PadronPreviewResponse:
    """Vista previa de importación (F1.3) sin persistir."""
    content = await file.read()
    try:
        filas = parse_padron_file(content, file.filename or "padron.csv")
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    preview = [
        FilaPadronPreview(
            nombre=f.nombre,
            apellidos=f.apellidos,
            email=f.email,
            comision=f.comision,
            regional=f.regional,
        )
        for f in filas
    ]
    return PadronPreviewResponse(total=len(preview), filas=preview)


@router.post(
    "/importar",
    response_model=PadronImportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("padron:importar"))],
)
async def importar_padron(
    request: Request,
    materia_id: Annotated[uuid.UUID, Form(...)],
    cohorte_id: Annotated[uuid.UUID, Form(...)],
    file: UploadFile = File(...),
    user: Annotated[CurrentUser, Depends(get_current_user)] = ...,
    db: Annotated[AsyncSession, Depends(get_db)] = ...,
) -> PadronImportResponse:
    content = await file.read()
    try:
        filas = parse_padron_file(content, file.filename or "padron.csv")
    except PadronParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    svc = PadronService(db, user.tenant_id)
    version = await svc.importar_padron(
        materia_id=materia_id,
        cohorte_id=cohorte_id,
        cargado_por=user.id,
        filas=filas,
    )
    entradas = await svc.list_entradas_activas(materia_id, cohorte_id)

    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.PADRON_CARGAR,
        detalle={
            "version_id": str(version.id),
            "materia_id": str(materia_id),
            "cohorte_id": str(cohorte_id),
            "filas": len(entradas),
        },
        materia_id=materia_id,
        filas_afectadas=len(entradas),
    )
    await db.commit()

    return PadronImportResponse(
        version=_version_response(version, len(entradas)),
        entradas=[_entrada_response(e) for e in entradas],
    )


@router.post(
    "/moodle/sync",
    response_model=PadronImportResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("padron:importar"))],
)
async def sync_moodle(
    body: MoodleSyncRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> PadronImportResponse:
    if not settings.moodle_base_url or not settings.moodle_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Moodle no configurado",
        )
    client = MoodleWSClient(settings.moodle_base_url, settings.moodle_token)
    svc = PadronService(db, user.tenant_id)
    try:
        version = await svc.importar_desde_moodle(
            materia_id=body.materia_id,
            cohorte_id=body.cohorte_id,
            cargado_por=user.id,
            client=client,
            course_id=body.moodle_course_id,
        )
    except MoodleUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    entradas = await svc.list_entradas_activas(body.materia_id, body.cohorte_id)
    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.PADRON_CARGAR,
        detalle={"origen": "moodle", "version_id": str(version.id)},
        materia_id=body.materia_id,
        filas_afectadas=len(entradas),
    )
    await db.commit()
    return PadronImportResponse(
        version=_version_response(version, len(entradas)),
        entradas=[_entrada_response(e) for e in entradas],
    )


@router.delete(
    "/materias/{materia_id}/datos",
    response_model=VaciarPadronResponse,
    dependencies=[Depends(require_permission("padron:vaciar"))],
)
async def vaciar_datos_materia(
    materia_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VaciarPadronResponse:
    """F1.5 / RN-04 — vacía padrón del actor en la materia."""
    svc = PadronService(db, user.tenant_id)
    count = await svc.vaciar_datos_materia(materia_id, user.id)
    await db.commit()
    return VaciarPadronResponse(versiones_eliminadas=count)


@router.patch(
    "/entradas/{entrada_id}",
    response_model=EntradaPadronResponse,
    dependencies=[Depends(require_permission("estructura:gestionar"))],
)
async def actualizar_comision_entrada(
    entrada_id: uuid.UUID,
    body: ActualizarComisionRequest,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EntradaPadronResponse:
    repo = EntradaPadronRepository(db, user.tenant_id)
    entrada = await repo.get(entrada_id)
    if entrada is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entrada no encontrada")

    entrada.comision = body.comision
    await db.flush()

    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.PADRON_ENTRADA_MODIFICAR,
        detalle={
            "entrada_id": str(entrada_id),
            "comision": body.comision,
        },
        filas_afectadas=1,
    )
    await db.commit()
    await db.refresh(entrada)
    return _entrada_response(entrada)
