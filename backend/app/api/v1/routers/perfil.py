"""Endpoints de perfil propio — C-20 (F11.1)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.schemas.perfil import PerfilResponse, PerfilUpdate
from app.services.perfil_service import PerfilService

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _perfil_response(usuario: object) -> PerfilResponse:
    return PerfilResponse(
        id=usuario.id,
        nombre=usuario.nombre,
        apellidos=usuario.apellidos,
        dni=usuario.dni,
        cuil=usuario.cuil,
        banco=usuario.banco,
        cbu=usuario.cbu,
        alias_cbu=usuario.alias_cbu,
        regional=usuario.regional,
        legajo=usuario.legajo,
        legajo_profesional=usuario.legajo_profesional,
        facturador=usuario.facturador,
        estado=usuario.estado,
        created_at=usuario.created_at,
        updated_at=usuario.updated_at,
    )


@router.get("", response_model=PerfilResponse)
async def obtener_perfil(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PerfilResponse:
    usuario = await PerfilService(db, user.tenant_id).obtener(user.id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _perfil_response(usuario)


@router.patch("", response_model=PerfilResponse)
async def actualizar_perfil(
    payload: PerfilUpdate,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PerfilResponse:
    usuario = await PerfilService(db, user.tenant_id).actualizar(user.id, payload)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    await db.commit()
    await db.refresh(usuario)
    return _perfil_response(usuario)
