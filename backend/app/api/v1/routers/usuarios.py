"""Endpoints de gestión de usuarios — C-07.

Guard: `usuarios:gestionar` (ADMIN only).
Flujo: Router → UsuarioService → UsuarioRepository → Usuario.
PII nunca aparece en respuestas ni logs de este módulo.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioResponse,
    UsuarioUpdate,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.usuario_service import UsuarioService

router = APIRouter(
    prefix="/api/admin/usuarios",
    tags=["usuarios"],
    dependencies=[Depends(require_permission("usuarios:gestionar"))],
)


def _usuario_response(entity) -> UsuarioResponse:
    return UsuarioResponse.model_validate(entity)


async def _audit(
    db: AsyncSession,
    user: CurrentUser,
    request: Request,
    *,
    accion: AuditAction,
    detalle: dict,
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
    )


@router.get("", response_model=UsuarioListResponse)
async def listar_usuarios(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioListResponse:
    svc = UsuarioService(db, user.tenant_id)
    items = [_usuario_response(u) for u in await svc.list_activos()]
    return UsuarioListResponse(items=items)


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    body: UsuarioCreate,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioResponse:
    svc = UsuarioService(db, user.tenant_id)
    nuevo = await svc.crear_usuario(body)
    await _audit(
        db,
        user,
        request,
        accion=AuditAction.USUARIO_CREAR,
        detalle={"usuario_id": str(nuevo.id)},
    )
    await db.commit()
    await db.refresh(nuevo)
    return _usuario_response(nuevo)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: uuid.UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioResponse:
    svc = UsuarioService(db, user.tenant_id)
    u = await svc.get(usuario_id)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")
    return _usuario_response(u)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: uuid.UUID,
    body: UsuarioUpdate,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UsuarioResponse:
    svc = UsuarioService(db, user.tenant_id)
    u = await svc.actualizar_usuario(usuario_id, body)
    if u is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")

    await _audit(
        db,
        user,
        request,
        accion=AuditAction.USUARIO_MODIFICAR,
        detalle={"usuario_id": str(usuario_id)},
    )
    await db.commit()
    await db.refresh(u)
    return _usuario_response(u)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def desactivar_usuario(
    usuario_id: uuid.UUID,
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    svc = UsuarioService(db, user.tenant_id)
    encontrado = await svc.desactivar_usuario(usuario_id)
    if not encontrado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No encontrado")

    await _audit(
        db,
        user,
        request,
        accion=AuditAction.USUARIO_DESACTIVAR,
        detalle={"usuario_id": str(usuario_id)},
    )
    await db.commit()
