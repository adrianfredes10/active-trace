"""RBAC fino: guard `require_permission` fail-closed (C-04).

Los permisos se resuelven server-side por request desde la matriz rol×permiso.
Cache por request vía `request.state` (no entre requests).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.services.permission_service import PermissionService


async def get_effective_permissions(
    request: Request,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> frozenset[str]:
    cached = getattr(request.state, "effective_permissions", None)
    if cached is not None:
        return cached
    perms = await PermissionService(db, user.tenant_id).effective_permissions(user.roles)
    request.state.effective_permissions = perms
    return perms


def require_permission(permission: str) -> Callable[..., None]:
    """Dependency factory: sin permiso explícito → 403."""

    async def _guard(
        permissions: Annotated[frozenset[str], Depends(get_effective_permissions)],
    ) -> None:
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permiso denegado",
            )

    return _guard
