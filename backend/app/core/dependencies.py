import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session_factory
from app.core.security import TOKEN_TYPE_ACCESS, TokenError, decode_token

# RESERVADO para C-04: require_permission — implementado en core/permissions.py

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()


@dataclass(frozen=True)
class CurrentUser:
    """Identidad derivada SOLO del JWT verificado (regla de oro).

    `id` es siempre el actor real (RN-41). Si hay impersonación activa,
    `impersonated_id` indica sobre quién se opera; la auditoría usa ambos.
    """

    id: uuid.UUID
    tenant_id: uuid.UUID
    roles: list[str] = field(default_factory=list)
    impersonated_id: uuid.UUID | None = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado"
        )
    try:
        claims = decode_token(credentials.credentials, expected_type=TOKEN_TYPE_ACCESS)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        ) from exc
    impersonated_raw = claims.get("impersonated_sub")
    return CurrentUser(
        id=uuid.UUID(claims["sub"]),
        tenant_id=uuid.UUID(claims["tenant_id"]),
        roles=list(claims.get("roles", [])),
        impersonated_id=(
            uuid.UUID(impersonated_raw) if impersonated_raw else None
        ),
    )
