import time

import pyotp
import pytest

from app.core.config import Settings
from app.core.security import (
    TOKEN_TYPE_ACCESS,
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
    verify_password,
    verify_totp,
)


def test_hash_password_round_trip(settings: Settings) -> None:
    h = hash_password("S3cret!")
    assert h != "S3cret!"
    assert verify_password("S3cret!", h) is True
    assert verify_password("otra", h) is False


def test_verify_password_with_garbage_hash(settings: Settings) -> None:
    assert verify_password("x", "not-a-valid-hash") is False


def test_access_token_has_minimal_claims(settings: Settings) -> None:
    token = create_access_token(user_id="u1", tenant_id="t1", roles=["ADMIN"])
    claims = decode_token(token, expected_type=TOKEN_TYPE_ACCESS)
    assert claims["sub"] == "u1"
    assert claims["tenant_id"] == "t1"
    assert claims["roles"] == ["ADMIN"]
    assert claims["type"] == TOKEN_TYPE_ACCESS
    assert "exp" in claims


def test_decode_rejects_wrong_type(settings: Settings) -> None:
    challenge = create_challenge_token(user_id="u1", tenant_id="t1")
    with pytest.raises(TokenError):
        decode_token(challenge, expected_type=TOKEN_TYPE_ACCESS)


def test_decode_rejects_tampered_token(settings: Settings) -> None:
    token = create_access_token(user_id="u1", tenant_id="t1")
    with pytest.raises(TokenError):
        decode_token(token + "x", expected_type=TOKEN_TYPE_ACCESS)


def test_email_blind_index_is_deterministic_and_normalized(settings: Settings) -> None:
    a = email_blind_index("Alumno@Activia.test")
    b = email_blind_index("  alumno@activia.test  ")
    assert a == b
    assert "alumno@activia.test" not in a


def test_opaque_token_hash_is_stable(settings: Settings) -> None:
    raw = generate_opaque_token()
    assert raw != hash_token(raw)
    assert hash_token(raw) == hash_token(raw)


def test_verify_totp(settings: Settings) -> None:
    secret = generate_totp_secret()
    valid_code = pyotp.TOTP(secret).now()
    assert verify_totp(secret, valid_code) is True
    assert verify_totp(secret, "000000") is False
