import uuid

import pyotp
import pytest

from app.core.database import get_session_factory
from app.core.security import email_blind_index, generate_totp_secret, hash_password
from app.models import Tenant, Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.services.auth_service import AuthService

pytestmark = pytest.mark.asyncio

SLUG = "acme"
TENANT_ID = uuid.UUID("00000000-0000-0000-0000-0000000000d3")
EMAIL = "alumno@acme.test"
PW = "S3cret!pass"


async def _seed(*, twofa: bool = False, totp: str | None = None) -> None:
    factory = get_session_factory()
    async with factory() as session:
        session.add(Tenant(id=TENANT_ID, nombre="Acme", slug=SLUG))
        await session.flush()
        await UsuarioRepository(session, TENANT_ID).add(
            Usuario(
                email=EMAIL,
                email_hash=email_blind_index(EMAIL),
                password_hash=hash_password(PW),
                is_active=True,
                two_factor_enabled=twofa,
                totp_secret=totp,
            )
        )
        await session.commit()


async def test_login_success(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": EMAIL, "password": PW},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["requires_2fa"] is False
    assert body["access_token"] and body["refresh_token"]


async def test_login_wrong_password(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": EMAIL, "password": "mala"},
    )
    assert resp.status_code == 401


async def test_login_unknown_tenant(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": "nope", "email": EMAIL, "password": PW},
    )
    assert resp.status_code == 401


async def test_login_rejects_extra_fields(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": EMAIL, "password": PW, "x": 1},
    )
    assert resp.status_code == 422


async def test_refresh_invalid_token(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/refresh", json={"refresh_token": "x"}
    )
    assert resp.status_code == 401


async def test_refresh_flow(api_client) -> None:
    await _seed()
    login = (
        await api_client.post(
            "/api/auth/login",
            json={"tenant_slug": SLUG, "email": EMAIL, "password": PW},
        )
    ).json()
    resp = await api_client.post(
        "/api/auth/refresh",
        json={"refresh_token": login["refresh_token"]},
    )
    assert resp.status_code == 200
    assert resp.json()["refresh_token"] != login["refresh_token"]


async def test_enroll_requires_auth(api_client) -> None:
    await _seed()
    resp = await api_client.post("/api/auth/2fa/enroll")
    assert resp.status_code == 401


async def test_rate_limit_blocks_after_5(api_client) -> None:
    await _seed()
    payload = {"tenant_slug": SLUG, "email": EMAIL, "password": "mala"}
    statuses = [
        (await api_client.post("/api/auth/login", json=payload)).status_code
        for _ in range(6)
    ]
    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429


async def test_2fa_full_flow(api_client) -> None:
    secret = generate_totp_secret()
    await _seed(twofa=True, totp=secret)
    login = (
        await api_client.post(
            "/api/auth/login",
            json={"tenant_slug": SLUG, "email": EMAIL, "password": PW},
        )
    ).json()
    assert login["requires_2fa"] is True
    resp = await api_client.post(
        "/api/auth/2fa/verify",
        json={"challenge_token": login["challenge_token"], "code": pyotp.TOTP(secret).now()},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_forgot_password_is_generic(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/forgot-password",
        json={"tenant_slug": SLUG, "email": "desconocido@acme.test"},
    )
    assert resp.status_code == 200


async def _login_tokens(api_client) -> dict:
    return (
        await api_client.post(
            "/api/auth/login",
            json={"tenant_slug": SLUG, "email": EMAIL, "password": PW},
        )
    ).json()


async def test_logout_then_refresh_fails(api_client) -> None:
    await _seed()
    tokens = await _login_tokens(api_client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    out = await api_client.post(
        "/api/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers
    )
    assert out.status_code == 200
    again = await api_client.post(
        "/api/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert again.status_code == 401


async def test_refresh_invalid_token_with_valid_session(api_client) -> None:
    await _seed()
    tokens = await _login_tokens(api_client)
    resp = await api_client.post(
        "/api/auth/refresh", json={"refresh_token": "inexistente"}
    )
    assert resp.status_code == 401


async def test_enroll_and_confirm_2fa_via_api(api_client) -> None:
    await _seed()
    tokens = await _login_tokens(api_client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    enroll = await api_client.post("/api/auth/2fa/enroll", headers=headers)
    assert enroll.status_code == 200
    secret = enroll.json()["secret"]
    confirm = await api_client.post(
        "/api/auth/2fa/confirm",
        json={"code": pyotp.TOTP(secret).now()},
        headers=headers,
    )
    assert confirm.status_code == 200


async def test_confirm_2fa_wrong_code_via_api(api_client) -> None:
    await _seed()
    tokens = await _login_tokens(api_client)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    await api_client.post("/api/auth/2fa/enroll", headers=headers)
    resp = await api_client.post(
        "/api/auth/2fa/confirm", json={"code": "000000"}, headers=headers
    )
    assert resp.status_code == 401


async def test_2fa_verify_wrong_code(api_client) -> None:
    secret = generate_totp_secret()
    await _seed(twofa=True, totp=secret)
    login = await _login_tokens(api_client)
    resp = await api_client.post(
        "/api/auth/2fa/verify",
        json={"challenge_token": login["challenge_token"], "code": "000000"},
    )
    assert resp.status_code == 401


async def test_2fa_verify_bad_challenge(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/2fa/verify",
        json={"challenge_token": "no-es-token", "code": "000000"},
    )
    assert resp.status_code == 401


async def test_reset_password_invalid_token(api_client) -> None:
    await _seed()
    resp = await api_client.post(
        "/api/auth/reset-password",
        json={"token": "no-existe", "new_password": "NuevaPass!9"},
    )
    assert resp.status_code == 401


async def test_reset_password_flow(api_client) -> None:
    await _seed()
    factory = get_session_factory()
    async with factory() as session:
        raw = await AuthService(session, TENANT_ID).forgot_password(EMAIL)
        await session.commit()
    assert raw is not None
    resp = await api_client.post(
        "/api/auth/reset-password",
        json={"token": raw, "new_password": "NuevaPass!9"},
    )
    assert resp.status_code == 200
    # login con nueva contraseña funciona
    ok = await api_client.post(
        "/api/auth/login",
        json={"tenant_slug": SLUG, "email": EMAIL, "password": "NuevaPass!9"},
    )
    assert ok.status_code == 200
