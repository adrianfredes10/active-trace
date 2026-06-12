"""Servicio de auditoría append-only (C-05)."""

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser
from app.models import AuditLog
from app.repositories.audit_repository import AuditLogRepository


class InvalidAuditAction(ValueError):
    pass


@dataclass(frozen=True)
class AuditContext:
    actor_id: uuid.UUID
    tenant_id: uuid.UUID
    impersonado_id: uuid.UUID | None = None
    ip: str | None = None
    user_agent: str | None = None

    @classmethod
    def from_user(
        cls,
        user: CurrentUser,
        *,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> "AuditContext":
        return cls(
            actor_id=user.id,
            tenant_id=user.tenant_id,
            impersonado_id=user.impersonated_id,
            ip=ip,
            user_agent=user_agent,
        )


class AuditService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.repo = AuditLogRepository(session, tenant_id)

    async def record(
        self,
        ctx: AuditContext,
        *,
        accion: AuditAction | str,
        detalle: dict | None = None,
        filas_afectadas: int = 0,
        materia_id: uuid.UUID | None = None,
    ) -> AuditLog:
        code = accion.value if isinstance(accion, AuditAction) else accion
        if code not in {a.value for a in AuditAction}:
            raise InvalidAuditAction(f"Código de acción no permitido: {code}")
        entry = AuditLog(
            actor_id=ctx.actor_id,
            impersonado_id=ctx.impersonado_id,
            materia_id=materia_id,
            accion=code,
            detalle=detalle,
            filas_afectadas=filas_afectadas,
            ip=ctx.ip,
            user_agent=ctx.user_agent,
        )
        return await self.repo.append(entry)
