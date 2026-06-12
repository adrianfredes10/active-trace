"""Endpoints de consulta del audit log (C-05)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.repositories.audit_repository import AuditLogRepository
from app.schemas.audit import AuditLogItem, AuditLogListResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    dependencies=[Depends(require_permission("auditoria:ver"))],
)
async def list_audit_logs(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
) -> AuditLogListResponse:
    rows = await AuditLogRepository(db, user.tenant_id).list_recent(limit=limit)
    items = [
        AuditLogItem(
            id=r.id,
            fecha_hora=r.fecha_hora,
            actor_id=r.actor_id,
            impersonado_id=r.impersonado_id,
            materia_id=r.materia_id,
            accion=r.accion,
            detalle=r.detalle,
            filas_afectadas=r.filas_afectadas,
            ip=r.ip,
        )
        for r in rows
    ]
    return AuditLogListResponse(items=items)
