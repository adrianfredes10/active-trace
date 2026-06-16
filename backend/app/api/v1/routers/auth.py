"""Endpoints de autenticación (C-03). Sin lógica de negocio: delega en AuthService."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core.dependencies import CurrentUser, get_current_user, get_db
from app.core.permissions import require_permission
from app.core.rate_limit import login_rate_limiter
from app.core.security import (
    TOKEN_TYPE_CHALLENGE,
    TokenError,
    decode_token,
    hash_token,
)
from app.models import PasswordResetToken, Tenant
from app.repositories.token_repository import RefreshTokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import (
    Enroll2FAResponse,
    ForgotPasswordRequest,
    ImpersonateAccessResponse,
    ImpersonateStartRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    TwoFactorConfirmRequest,
    TwoFactorVerifyRequest,
)
from app.services.audit_service import AuditContext, AuditService
from app.services.auth_service import AuthService, InvalidCredentials

router = APIRouter(prefix="/api/auth", tags=["auth"])

_INVALID = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
)


async def _find_tenant_id(db: AsyncSession, slug: str) -> uuid.UUID | None:
    normalized = slug.strip().lower()
    result = await db.execute(
        select(Tenant.id).where(Tenant.slug == normalized, Tenant.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def _resolve_tenant_id(db: AsyncSession, slug: str) -> uuid.UUID:
    tenant_id = await _find_tenant_id(db, slug)
    if tenant_id is None:
        raise _INVALID
    return tenant_id


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    if not login_rate_limiter.allow(f"{client_ip}:{payload.email.lower()}"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos, probá más tarde",
        )
    tenant_id = await _resolve_tenant_id(db, payload.tenant_slug)
    try:
        result = await AuthService(db, tenant_id).login(payload.email, payload.password)
    except InvalidCredentials as exc:
        raise _INVALID from exc
    await db.commit()
    if result.requires_2fa:
        return LoginResponse(requires_2fa=True, challenge_token=result.challenge_token)
    assert result.tokens is not None
    return LoginResponse(
        access_token=result.tokens.access_token,
        refresh_token=result.tokens.refresh_token,
    )


@router.post("/2fa/verify", response_model=TokenResponse)
async def verify_2fa(
    payload: TwoFactorVerifyRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    # tenant del challenge token; AuthService valida el token internamente
    try:
        claims = decode_token(payload.challenge_token, expected_type=TOKEN_TYPE_CHALLENGE)
    except TokenError as exc:
        raise _INVALID from exc
    tenant_id = uuid.UUID(claims["tenant_id"])
    try:
        tokens = await AuthService(db, tenant_id).verify_2fa(
            payload.challenge_token, payload.code
        )
    except InvalidCredentials as exc:
        raise _INVALID from exc
    await db.commit()
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    row = await RefreshTokenRepository.get_by_hash_global(
        db, hash_token(payload.refresh_token)
    )
    if row is None:
        raise _INVALID
    try:
        tokens = await AuthService(db, row.tenant_id).refresh(payload.refresh_token)
    except InvalidCredentials as exc:
        await db.commit()  # persistir la invalidación de cadena ante reuso
        raise _INVALID from exc
    await db.commit()
    return TokenResponse(
        access_token=tokens.access_token, refresh_token=tokens.refresh_token
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    payload: LogoutRequest, user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    await AuthService(db, user.tenant_id).logout(payload.refresh_token)
    await db.commit()
    return MessageResponse(detail="Sesión cerrada")


@router.post("/2fa/enroll", response_model=Enroll2FAResponse)
async def enroll_2fa(
    user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Enroll2FAResponse:
    svc = AuthService(db, user.tenant_id)
    usuario = await UsuarioRepository(db, user.tenant_id).get(user.id)
    if usuario is None:
        raise _INVALID
    enroll = await svc.enroll_2fa(usuario)
    await db.commit()
    return Enroll2FAResponse(secret=enroll.secret, provisioning_uri=enroll.provisioning_uri)


@router.post("/2fa/confirm", response_model=MessageResponse)
async def confirm_2fa(
    payload: TwoFactorConfirmRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    svc = AuthService(db, user.tenant_id)
    usuario = await UsuarioRepository(db, user.tenant_id).get(user.id)
    if usuario is None:
        raise _INVALID
    try:
        await svc.confirm_2fa(usuario, payload.code)
    except InvalidCredentials as exc:
        raise _INVALID from exc
    await db.commit()
    return MessageResponse(detail="2FA activado")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    tenant_id = await _find_tenant_id(db, payload.tenant_slug)
    if tenant_id is not None:
        await AuthService(db, tenant_id).forgot_password(payload.email)
        await db.commit()
    # respuesta genérica: no revela si el email/tenant existe
    return MessageResponse(detail="Si la cuenta existe, se enviaron instrucciones")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    # el reset token es global-único; buscamos el tenant del token vía el usuario
    result = await db.execute(
        select(PasswordResetToken.tenant_id).where(
            PasswordResetToken.token_hash == hash_token(payload.token)
        )
    )
    tenant_id = result.scalar_one_or_none()
    if tenant_id is None:
        raise _INVALID
    try:
        await AuthService(db, tenant_id).reset_password(payload.token, payload.new_password)
    except InvalidCredentials as exc:
        raise _INVALID from exc
    await db.commit()
    return MessageResponse(detail="Contraseña actualizada")


@router.post(
    "/impersonate/start",
    response_model=ImpersonateAccessResponse,
    dependencies=[Depends(require_permission("impersonacion:usar"))],
)
async def impersonate_start(
    payload: ImpersonateStartRequest,
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImpersonateAccessResponse:
    try:
        target_id = uuid.UUID(payload.target_user_id)
    except ValueError as exc:
        raise _INVALID from exc
    svc = AuthService(db, user.tenant_id)
    try:
        access = await svc.start_impersonation(user.id, target_id, user.roles)
    except InvalidCredentials as exc:
        raise _INVALID from exc
    ctx = AuditContext(
        actor_id=user.id,
        tenant_id=user.tenant_id,
        impersonado_id=target_id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.IMPERSONACION_INICIAR,
        detalle={"impersonado_id": str(target_id)},
    )
    await db.commit()
    return ImpersonateAccessResponse(
        access_token=access,
        impersonated_id=str(target_id),
    )


@router.post("/impersonate/stop", response_model=ImpersonateAccessResponse)
async def impersonate_stop(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ImpersonateAccessResponse:
    if user.impersonated_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay impersonación activa",
        )
    svc = AuthService(db, user.tenant_id)
    access = await svc.stop_impersonation(user.id, user.roles)
    ctx = AuditContext.from_user(
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await AuditService(db, user.tenant_id).record(
        ctx,
        accion=AuditAction.IMPERSONACION_FINALIZAR,
        detalle={"impersonado_id": str(user.impersonated_id)},
    )
    await db.commit()
    return ImpersonateAccessResponse(access_token=access)
