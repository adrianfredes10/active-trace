import uuid
from datetime import datetime, timedelta, timezone

import pyotp
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    email_blind_index,
    generate_totp_secret,
    hash_password,
    hash_token,
)
from app.models import RefreshToken, Tenant, Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService, InvalidCredentials

TENANT = uuid.UUID("00000000-0000-0000-0000-0000000000c3")
EMAIL = "alumno@activia.test"
PW = "S3cret!pass"

pytestmark = pytest.mark.asyncio


async def _setup(
    session: AsyncSession,
    *,
    active: bool = True,
    twofa: bool = False,
    totp: str | None = None,
) -> Usuario:
    session.add(Tenant(id=TENANT, nombre="C", slug="c"))
    await session.flush()
    repo = UsuarioRepository(session, TENANT)
    user = Usuario(
        email=EMAIL,
        email_hash=email_blind_index(EMAIL),
        password_hash=hash_password(PW),
        is_active=active,
        two_factor_enabled=twofa,
        totp_secret=totp,
    )
    await repo.add(user)
    await session.flush()
    return user


async def test_login_success_returns_tokens(session: AsyncSession, settings) -> None:
    await _setup(session)
    result = await AuthService(session, TENANT).login(EMAIL, PW)
    assert result.requires_2fa is False
    assert result.tokens is not None
    assert result.tokens.access_token and result.tokens.refresh_token


async def test_login_wrong_password(session: AsyncSession, settings) -> None:
    await _setup(session)
    with pytest.raises(InvalidCredentials):
        await AuthService(session, TENANT).login(EMAIL, "mala")


async def test_login_inactive_user(session: AsyncSession, settings) -> None:
    await _setup(session, active=False)
    with pytest.raises(InvalidCredentials):
        await AuthService(session, TENANT).login(EMAIL, PW)


async def test_login_unknown_email(session: AsyncSession, settings) -> None:
    await _setup(session)
    with pytest.raises(InvalidCredentials):
        await AuthService(session, TENANT).login("nadie@activia.test", PW)


async def test_login_with_2fa_returns_challenge(session: AsyncSession, settings) -> None:
    secret = generate_totp_secret()
    await _setup(session, twofa=True, totp=secret)
    result = await AuthService(session, TENANT).login(EMAIL, PW)
    assert result.requires_2fa is True
    assert result.challenge_token is not None
    assert result.tokens is None


async def test_verify_2fa_success(session: AsyncSession, settings) -> None:
    secret = generate_totp_secret()
    await _setup(session, twofa=True, totp=secret)
    svc = AuthService(session, TENANT)
    challenge = (await svc.login(EMAIL, PW)).challenge_token
    assert challenge is not None
    tokens = await svc.verify_2fa(challenge, pyotp.TOTP(secret).now())
    assert tokens.access_token and tokens.refresh_token


async def test_verify_2fa_wrong_code(session: AsyncSession, settings) -> None:
    secret = generate_totp_secret()
    await _setup(session, twofa=True, totp=secret)
    svc = AuthService(session, TENANT)
    challenge = (await svc.login(EMAIL, PW)).challenge_token
    with pytest.raises(InvalidCredentials):
        await svc.verify_2fa(challenge, "000000")


async def test_verify_2fa_bad_challenge_token(session: AsyncSession, settings) -> None:
    secret = generate_totp_secret()
    await _setup(session, twofa=True, totp=secret)
    with pytest.raises(InvalidCredentials):
        await AuthService(session, TENANT).verify_2fa("not-a-token", "000000")


async def test_refresh_rotates_and_revokes_old(session: AsyncSession, settings) -> None:
    await _setup(session)
    svc = AuthService(session, TENANT)
    first = (await svc.login(EMAIL, PW)).tokens
    assert first is not None
    second = await svc.refresh(first.refresh_token)
    assert second.refresh_token != first.refresh_token
    # el viejo quedó revocado
    old = await svc.refresh_tokens.get_by_hash(hash_token(first.refresh_token))
    assert old is not None and old.revoked_at is not None


async def test_refresh_reuse_detection_invalidates_chain(
    session: AsyncSession, settings
) -> None:
    await _setup(session)
    svc = AuthService(session, TENANT)
    first = (await svc.login(EMAIL, PW)).tokens
    assert first is not None
    second = await svc.refresh(first.refresh_token)
    # reusar el viejo (ya revocado) dispara invalidación de toda la cadena
    with pytest.raises(InvalidCredentials):
        await svc.refresh(first.refresh_token)
    # el nuevo también quedó inutilizado
    with pytest.raises(InvalidCredentials):
        await svc.refresh(second.refresh_token)


async def test_refresh_expired(session: AsyncSession, settings) -> None:
    user = await _setup(session)
    svc = AuthService(session, TENANT)
    raw = "expired-raw-token"
    await svc.refresh_tokens.add(
        RefreshToken(
            usuario_id=user.id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
    )
    await session.flush()
    with pytest.raises(InvalidCredentials):
        await svc.refresh(raw)


async def test_refresh_unknown_token(session: AsyncSession, settings) -> None:
    await _setup(session)
    with pytest.raises(InvalidCredentials):
        await AuthService(session, TENANT).refresh("inexistente")


async def test_logout_revokes(session: AsyncSession, settings) -> None:
    await _setup(session)
    svc = AuthService(session, TENANT)
    tokens = (await svc.login(EMAIL, PW)).tokens
    assert tokens is not None
    await svc.logout(tokens.refresh_token)
    with pytest.raises(InvalidCredentials):
        await svc.refresh(tokens.refresh_token)


async def test_enroll_and_confirm_2fa(session: AsyncSession, settings) -> None:
    user = await _setup(session)
    svc = AuthService(session, TENANT)
    enroll = await svc.enroll_2fa(user)
    assert enroll.secret and enroll.provisioning_uri.startswith("otpauth://")
    assert user.two_factor_enabled is False
    await svc.confirm_2fa(user, pyotp.TOTP(enroll.secret).now())
    assert user.two_factor_enabled is True


async def test_confirm_2fa_wrong_code(session: AsyncSession, settings) -> None:
    user = await _setup(session)
    svc = AuthService(session, TENANT)
    await svc.enroll_2fa(user)
    with pytest.raises(InvalidCredentials):
        await svc.confirm_2fa(user, "000000")


async def test_forgot_and_reset_password(session: AsyncSession, settings) -> None:
    await _setup(session)
    svc = AuthService(session, TENANT)
    raw = await svc.forgot_password(EMAIL)
    assert raw is not None
    await svc.reset_password(raw, "NuevaPass!9")
    # login viejo falla, nuevo funciona
    with pytest.raises(InvalidCredentials):
        await svc.login(EMAIL, PW)
    assert (await svc.login(EMAIL, "NuevaPass!9")).tokens is not None


async def test_forgot_unknown_email_returns_none(
    session: AsyncSession, settings
) -> None:
    await _setup(session)
    assert await AuthService(session, TENANT).forgot_password("x@y.test") is None


async def test_reset_token_single_use(session: AsyncSession, settings) -> None:
    await _setup(session)
    svc = AuthService(session, TENANT)
    raw = await svc.forgot_password(EMAIL)
    assert raw is not None
    await svc.reset_password(raw, "NuevaPass!9")
    with pytest.raises(InvalidCredentials):
        await svc.reset_password(raw, "OtraMas!10")
