"""Endpoints de guardias — C-13."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.guardia import (
    GuardiaCreate,
    GuardiaListResponse,
    GuardiaResponse,
    GuardiaUpdate,
)
from app.services.guardia_service import GuardiaService

router = APIRouter(prefix="/api/guardias", tags=["guardias"])


def _guardia_response(g: object) -> GuardiaResponse:
    return GuardiaResponse(
        id=g.id,
        asignacion_id=g.asignacion_id,
        materia_id=g.materia_id,
        carrera_id=g.carrera_id,
        cohorte_id=g.cohorte_id,
        dia=g.dia.value if hasattr(g.dia, "value") else str(g.dia),
        horario=g.horario,
        estado=g.estado.value if hasattr(g.estado, "value") else str(g.estado),
        comentarios=g.comentarios,
        creada_at=g.creada_at,
    )


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
    )


@router.post(
    "",
    response_model=GuardiaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("guardias:registrar"))],
)
async def registrar_guardia(
    body: GuardiaCreate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuardiaResponse:
    svc = GuardiaService(db, user.tenant_id)
    try:
        guardia = await svc.registrar(
            user=user,
            asignacion_id=body.asignacion_id,
            materia_id=body.materia_id,
            carrera_id=body.carrera_id,
            cohorte_id=body.cohorte_id,
            dia=body.dia,
            horario=body.horario,
            comentarios=body.comentarios,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return _guardia_response(guardia)


@router.get(
    "",
    response_model=GuardiaListResponse,
    dependencies=[Depends(require_permission("guardias:registrar"))],
)
async def listar_guardias(
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    asignacion_id: uuid.UUID | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GuardiaListResponse:
    svc = GuardiaService(db, user.tenant_id)
    try:
        items = await svc.listar(
            user,
            materia_id=materia_id,
            cohorte_id=cohorte_id,
            asignacion_id=asignacion_id,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    return GuardiaListResponse(items=[_guardia_response(g) for g in items])


@router.patch(
    "/{guardia_id}",
    response_model=GuardiaResponse,
    dependencies=[Depends(require_permission("guardias:registrar"))],
)
async def actualizar_guardia(
    guardia_id: uuid.UUID,
    body: GuardiaUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuardiaResponse:
    svc = GuardiaService(db, user.tenant_id)
    try:
        guardia = await svc.actualizar(
            guardia_id,
            user=user,
            estado=body.estado,
            comentarios=body.comentarios,
        )
    except (ValueError, PermissionError) as exc:
        raise _http_error(exc) from exc
    await db.commit()
    return _guardia_response(guardia)


@router.get(
    "/export",
    dependencies=[Depends(require_permission("encuentros:gestionar"))],
)
async def exportar_guardias(
    materia_id: uuid.UUID | None = None,
    cohorte_id: uuid.UUID | None = None,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    svc = GuardiaService(db, user.tenant_id)
    items = await svc.listar(user, materia_id=materia_id, cohorte_id=cohorte_id)
    content = svc.exportar_csv(items)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="guardias.csv"'},
    )
