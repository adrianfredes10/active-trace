"""Endpoints de encuentros — C-13."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.encuentro import (
    EncuentroUnicoCreate,
    HtmlEncuentrosResponse,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    InstanciaListResponse,
    SlotEncuentroResponse,
    SlotRecurrenteCreate,
)
from app.services.encuentro_service import EncuentroService

router = APIRouter(prefix="/api/encuentros", tags=["encuentros"])
_GUARD = [Depends(require_permission("encuentros:gestionar"))]


def _instancia_response(i: object) -> InstanciaEncuentroResponse:
    return InstanciaEncuentroResponse(
        id=i.id,
        slot_id=i.slot_id,
        materia_id=i.materia_id,
        fecha=i.fecha,
        hora=i.hora,
        titulo=i.titulo,
        estado=i.estado.value if hasattr(i.estado, "value") else str(i.estado),
        meet_url=i.meet_url,
        video_url=i.video_url,
        comentario=i.comentario,
    )


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


@router.post(
    "/recurrente",
    response_model=SlotEncuentroResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GUARD,
)
async def crear_recurrente(
    body: SlotRecurrenteCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SlotEncuentroResponse:
    svc = EncuentroService(db, user.tenant_id)
    try:
        slot, instancias = await svc.crear_recurrente(
            user=user,
            asignacion_id=body.asignacion_id,
            materia_id=body.materia_id,
            titulo=body.titulo,
            hora=body.hora,
            dia_semana=body.dia_semana,
            fecha_inicio=body.fecha_inicio,
            cant_semanas=body.cant_semanas,
            meet_url=body.meet_url,
            vig_desde=body.vig_desde,
            vig_hasta=body.vig_hasta,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return SlotEncuentroResponse(
        id=slot.id,
        materia_id=slot.materia_id,
        titulo=slot.titulo,
        instancias_generadas=len(instancias),
    )


@router.post(
    "/unico",
    response_model=InstanciaEncuentroResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_GUARD,
)
async def crear_unico(
    body: EncuentroUnicoCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InstanciaEncuentroResponse:
    svc = EncuentroService(db, user.tenant_id)
    try:
        instancia = await svc.crear_unico(
            user=user,
            asignacion_id=body.asignacion_id,
            materia_id=body.materia_id,
            titulo=body.titulo,
            fecha=body.fecha,
            hora=body.hora,
            meet_url=body.meet_url,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return _instancia_response(instancia)


@router.patch(
    "/instancias/{instancia_id}",
    response_model=InstanciaEncuentroResponse,
    dependencies=_GUARD,
)
async def editar_instancia(
    instancia_id: uuid.UUID,
    body: InstanciaEncuentroUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InstanciaEncuentroResponse:
    svc = EncuentroService(db, user.tenant_id)
    try:
        instancia = await svc.actualizar_instancia(
            instancia_id,
            user=user,
            estado=body.estado,
            meet_url=body.meet_url,
            video_url=body.video_url,
            comentario=body.comentario,
        )
    except ValueError as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return _instancia_response(instancia)


@router.get(
    "/instancias",
    response_model=InstanciaListResponse,
    dependencies=_GUARD,
)
async def listar_instancias(
    materia_id: uuid.UUID,
    desde: date | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaListResponse:
    items = await EncuentroService(db, user.tenant_id).listar_por_materia(
        materia_id, desde=desde
    )
    return InstanciaListResponse(items=[_instancia_response(i) for i in items])


@router.get(
    "/admin",
    response_model=InstanciaListResponse,
    dependencies=_GUARD,
)
async def listar_admin(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InstanciaListResponse:
    svc = EncuentroService(db, user.tenant_id)
    try:
        items = await svc.listar_admin(user)
    except PermissionError as exc:
        raise _http_error(exc) from exc
    return InstanciaListResponse(items=[_instancia_response(i) for i in items])


@router.get(
    "/html/{materia_id}",
    response_model=HtmlEncuentrosResponse,
    dependencies=_GUARD,
)
async def html_aula_virtual(
    materia_id: uuid.UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HtmlEncuentrosResponse:
    svc = EncuentroService(db, user.tenant_id)
    items = await svc.listar_por_materia(materia_id)
    return HtmlEncuentrosResponse(html=svc.generar_html(items))
