"""Lógica de autenticación (C-03).

Flujo unidireccional: el router llama al service; el service usa repositories.
Identidad/tenant del contexto, nunca del dato de entrada.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    TOKEN_TYPE_CHALLENGE,
    TokenError,
    create_access_token,
    create_challenge_token,
    decode_token,
    email_blind_index,
    generate_opaque_token,
    generate_totp_secret,
    hash_password,
    hash_token,
    totp_provisioning_uri,
    verify_password,
    verify_totp,
)
from app.models import PasswordResetToken, RefreshToken, Usuario
from app.repositories.rbac_repository import UsuarioRolRepository
from app.repositories.token_repository import (
    PasswordResetTokenRepository,
    RefreshTokenRepository,
)
from app.repositories.usuario_repository import UsuarioRepository


class AuthError(Exception):
    """Error de autenticación genérico (no revela detalles al cliente)."""


class InvalidCredentials(AuthError):
    pass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class LoginResult:
    requires_2fa: bool
    tokens: TokenPair | None = None
    challenge_token: str | None = None


@dataclass(frozen=True)
class EnrollResult:
    secret: str
    provisioning_uri: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AuthService:
    def __init__(self, session: AsyncSession, tenant_id: uuid.UUID) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.users = UsuarioRepository(session, tenant_id)
        self.usuario_roles = UsuarioRolRepository(session, tenant_id)
        self.refresh_tokens = RefreshTokenRepository(session, tenant_id)
        self.reset_tokens = PasswordResetTokenRepository(session, tenant_id)

    # -- credenciales ------------------------------------------------------- #

    async def _authenticate(self, email: str, password: str) -> Usuario:
        user = await self.users.get_by_email_hash(email_blind_index(email))
        if (
            user is None
            or not user.is_active
            or not verify_password(password, user.password_hash)
        ):
            raise InvalidCredentials()
        return user

    async def login(self, email: str, password: str) -> LoginResult:
        user = await self._authenticate(email, password)
        if user.two_factor_enabled:
            challenge = create_challenge_token(
                user_id=str(user.id), tenant_id=str(self.tenant_id)
            )
            return LoginResult(requires_2fa=True, challenge_token=challenge)
        return LoginResult(requires_2fa=False, tokens=await self._issue_session(user))

    # -- sesión / refresh --------------------------------------------------- #

    async def _create_refresh(self, user: Usuario) -> tuple[str, RefreshToken]:
        raw = generate_opaque_token()
        ttl = timedelta(days=get_settings().refresh_token_expire_days)
        row = RefreshToken(
            usuario_id=user.id,
            token_hash=hash_token(raw),
            expires_at=_now() + ttl,
        )
        await self.refresh_tokens.add(row)
        return raw, row

    async def _user_role_codes(self, user: Usuario) -> list[str]:
        return await self.usuario_roles.list_role_codes_for_user(user.id)

    async def _issue_session(self, user: Usuario) -> TokenPair:
        roles = await self._user_role_codes(user)
        access = create_access_token(
            user_id=str(user.id), tenant_id=str(self.tenant_id), roles=roles
        )
        raw_refresh, _ = await self._create_refresh(user)
        return TokenPair(access_token=access, refresh_token=raw_refresh)

    async def refresh(self, raw_refresh: str) -> TokenPair:
        token = await self.refresh_tokens.get_by_hash(hash_token(raw_refresh))
        if token is None:
            raise InvalidCredentials()
        if token.revoked_at is not None:
            # reuso de un refresh revocado = señal de robo → invalida la cadena
            await self.refresh_tokens.revoke_all_for_user(token.usuario_id)
            raise InvalidCredentials()
        if token.expires_at <= _now():
            raise InvalidCredentials()
        user = await self.users.get(token.usuario_id)
        if user is None or not user.is_active:
            raise InvalidCredentials()
        roles = await self._user_role_codes(user)
        access = create_access_token(
            user_id=str(user.id), tenant_id=str(self.tenant_id), roles=roles
        )
        raw_new, new_row = await self._create_refresh(user)
        await self.refresh_tokens.revoke(token, replaced_by_id=new_row.id)
        return TokenPair(access_token=access, refresh_token=raw_new)

    async def logout(self, raw_refresh: str) -> None:
        token = await self.refresh_tokens.get_by_hash(hash_token(raw_refresh))
        if token is not None and token.revoked_at is None:
            await self.refresh_tokens.revoke(token)

    # -- 2FA ---------------------------------------------------------------- #

    async def enroll_2fa(self, user: Usuario) -> EnrollResult:
        secret = generate_totp_secret()
        user.totp_secret = secret
        await self.session.flush()
        uri = totp_provisioning_uri(
            secret, account_name=str(user.id), issuer="activia-trace"
        )
        return EnrollResult(secret=secret, provisioning_uri=uri)

    async def confirm_2fa(self, user: Usuario, code: str) -> None:
        if not user.totp_secret or not verify_totp(user.totp_secret, code):
            raise InvalidCredentials()
        user.two_factor_enabled = True
        await self.session.flush()

    async def verify_2fa(self, challenge_token: str, code: str) -> TokenPair:
        try:
            claims = decode_token(challenge_token, expected_type=TOKEN_TYPE_CHALLENGE)
        except TokenError as exc:
            raise InvalidCredentials() from exc
        user = await self.users.get(uuid.UUID(claims["sub"]))
        if (
            user is None
            or not user.is_active
            or not user.totp_secret
            or not verify_totp(user.totp_secret, code)
        ):
            raise InvalidCredentials()
        return await self._issue_session(user)

    # -- recuperación ------------------------------------------------------- #

    async def forgot_password(self, email: str) -> str | None:
        """Genera un token de reset si el email existe. Devuelve el token crudo
        (para el canal de envío); la respuesta del endpoint es genérica."""
        user = await self.users.get_by_email_hash(email_blind_index(email))
        if user is None or not user.is_active:
            return None
        raw = generate_opaque_token()
        ttl = timedelta(minutes=get_settings().password_reset_expire_minutes)
        await self.reset_tokens.add(
            PasswordResetToken(
                usuario_id=user.id,
                token_hash=hash_token(raw),
                expires_at=_now() + ttl,
            )
        )
        return raw

    async def reset_password(self, raw_token: str, new_password: str) -> None:
        token = await self.reset_tokens.get_by_hash(hash_token(raw_token))
        if token is None or token.used_at is not None or token.expires_at <= _now():
            raise InvalidCredentials()
        user = await self.users.get(token.usuario_id)
        if user is None:
            raise InvalidCredentials()
        user.password_hash = hash_password(new_password)
        await self.reset_tokens.mark_used(token)
        # invalida sesiones activas tras cambiar el password
        await self.refresh_tokens.revoke_all_for_user(user.id)
        await self.session.flush()

    # -- impersonación (C-05) ------------------------------------------------ #

    async def start_impersonation(
        self, actor_id: uuid.UUID, target_id: uuid.UUID, roles: list[str]
    ) -> str:
        actor = await self.users.get(actor_id)
        target = await self.users.get(target_id)
        if (
            actor is None
            or target is None
            or not actor.is_active
            or not target.is_active
            or actor_id == target_id
        ):
            raise InvalidCredentials()
        return create_access_token(
            user_id=str(actor_id),
            tenant_id=str(self.tenant_id),
            roles=roles,
            impersonated_id=str(target_id),
        )

    async def stop_impersonation(self, actor_id: uuid.UUID, roles: list[str]) -> str:
        actor = await self.users.get(actor_id)
        if actor is None or not actor.is_active:
            raise InvalidCredentials()
        return create_access_token(
            user_id=str(actor_id),
            tenant_id=str(self.tenant_id),
            roles=roles,
        )
