"""Endpoints de lectura RBAC (C-04)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.models import Permiso, Rol, RolPermiso
from app.repositories.rbac_repository import RolRepository
from app.schemas.rbac import (
    CatalogoResponse,
    MessageResponse,
    PermisosEfectivosResponse,
    RolCatalogItem,
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/api/rbac", tags=["rbac"])


@router.get("/permisos-efectivos", response_model=PermisosEfectivosResponse)
async def mis_permisos(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PermisosEfectivosResponse:
    perms = await PermissionService(db, user.tenant_id).effective_permissions(
        user.roles
    )
    return PermisosEfectivosResponse(permisos=sorted(perms), roles=sorted(user.roles))


@router.get("/catalogo", response_model=CatalogoResponse)
async def catalogo(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CatalogoResponse:
    roles = await RolRepository(db, user.tenant_id).list_all()
    items: list[RolCatalogItem] = []
    for rol in roles:
        result = await db.execute(
            select(Permiso.modulo, Permiso.accion)
            .join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
            .where(
                RolPermiso.tenant_id == user.tenant_id,
                RolPermiso.rol_id == rol.id,
                RolPermiso.deleted_at.is_(None),
                Permiso.deleted_at.is_(None),
            )
            .order_by(Permiso.modulo, Permiso.accion)
        )
        claves = [f"{m}:{a}" for m, a in result.all()]
        items.append(RolCatalogItem(codigo=rol.codigo, nombre=rol.nombre, permisos=claves))
    return CatalogoResponse(roles=items)


@router.get(
    "/demo-protegido",
    response_model=MessageResponse,
    dependencies=[Depends(require_permission("calificaciones:importar"))],
)
async def demo_protegido() -> MessageResponse:
    """Endpoint de prueba para validar require_permission (no es dominio)."""
    return MessageResponse(detail="ok")
