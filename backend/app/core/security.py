"""Primitivas de seguridad.

C-02: cifrado en reposo AES-256-GCM (PII/secretos `[cifrado]`).
C-03: hashing de passwords (Argon2id), JWT (access/challenge), blind index
de email (HMAC determinista) y TOTP (2FA).

Regla: los valores en claro (passwords, PII) NUNCA se escriben en logs.
"""

import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.types import String, TypeDecorator

from app.core.config import get_settings

_NONCE_SIZE = 12  # bytes, recomendado para AES-GCM
_JWT_ALGORITHM = "HS256"

# Tipos de token JWT (claim `type`)
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_CHALLENGE = "challenge"  # paso intermedio de 2FA


# --------------------------------------------------------------------------- #
# Cifrado en reposo (AES-256-GCM) — C-02
# --------------------------------------------------------------------------- #

class DecryptionError(Exception):
    """El texto cifrado no pudo descifrarse (clave incorrecta o manipulado)."""


def _encryption_key() -> bytes:
    # ENCRYPTION_KEY se valida con longitud exacta de 32 caracteres en config.
    return get_settings().encryption_key.encode("utf-8")


def encrypt(plaintext: str) -> str:
    """Cifra texto plano con AES-256-GCM y devuelve base64(nonce + ciphertext)."""
    aesgcm = AESGCM(_encryption_key())
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(token: str) -> str:
    """Descifra un token producido por `encrypt`. Falla si fue manipulado."""
    try:
        raw = base64.b64decode(token.encode("ascii"))
        nonce, ciphertext = raw[:_NONCE_SIZE], raw[_NONCE_SIZE:]
        aesgcm = AESGCM(_encryption_key())
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
    except (InvalidTag, ValueError) as exc:
        raise DecryptionError("No se pudo descifrar el valor") from exc


class EncryptedString(TypeDecorator[str]):
    """Columna que cifra al escribir y descifra al leer (cifrado transparente)."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect: object) -> str | None:
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value: str | None, dialect: object) -> str | None:
        if value is None:
            return None
        return decrypt(value)


# --------------------------------------------------------------------------- #
# Passwords (Argon2id) — C-03
# --------------------------------------------------------------------------- #

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Hashea un password con Argon2id."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica un password contra su hash Argon2id. No lanza ante mismatch."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


# --------------------------------------------------------------------------- #
# JWT (access / challenge) — C-03
# --------------------------------------------------------------------------- #

class TokenError(Exception):
    """Token JWT inválido, expirado o de tipo inesperado."""


def _secret() -> str:
    return get_settings().secret_key


def _encode(claims: dict[str, Any], token_type: str, expires: timedelta) -> str:
    payload = {
        **claims,
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _secret(), algorithm=_JWT_ALGORITHM)


def create_access_token(
    *,
    user_id: str,
    tenant_id: str,
    roles: list[str] | None = None,
    impersonated_id: str | None = None,
) -> str:
    """Access token JWT de vida corta con claims mínimos."""
    ttl = timedelta(minutes=get_settings().access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": roles or [],
    }
    if impersonated_id is not None:
        payload["impersonated_sub"] = impersonated_id
    return _encode(payload, TOKEN_TYPE_ACCESS, ttl)


def create_challenge_token(*, user_id: str, tenant_id: str) -> str:
    """Token intermedio de 2FA: válido solo para completar el segundo factor."""
    ttl = timedelta(minutes=get_settings().two_factor_challenge_expire_minutes)
    return _encode({"sub": user_id, "tenant_id": tenant_id}, TOKEN_TYPE_CHALLENGE, ttl)


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    """Decodifica y valida firma, expiración y el claim `type`."""
    try:
        claims = jwt.decode(token, _secret(), algorithms=[_JWT_ALGORITHM])
    except JWTError as exc:
        raise TokenError("Token inválido o expirado") from exc
    if claims.get("type") != expected_type:
        raise TokenError("Tipo de token inesperado")
    return claims


# --------------------------------------------------------------------------- #
# Tokens opacos (refresh / reset) — C-03
# --------------------------------------------------------------------------- #

def generate_opaque_token() -> str:
    """Token aleatorio opaco (refresh/reset). Solo se persiste su hash."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """SHA-256 hex del token opaco, para almacenar sin guardar el valor."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# Blind index (lookup sobre datos cifrados) — C-03
# --------------------------------------------------------------------------- #

def email_blind_index(email: str) -> str:
    """HMAC-SHA256 determinista del email normalizado (pepper = SECRET_KEY).

    Permite lookup por igualdad e índice único sobre un atributo cifrado,
    sin ser reversible al valor original.
    """
    normalized = email.strip().lower()
    pepper = _secret().encode("utf-8")
    return hmac.new(pepper, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


# --------------------------------------------------------------------------- #
# TOTP (2FA) — C-03
# --------------------------------------------------------------------------- #

def generate_totp_secret() -> str:
    """Secreto base32 para TOTP."""
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, *, account_name: str, issuer: str) -> str:
    """URI otpauth:// para configurar el autenticador (QR)."""
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)


def verify_totp(secret: str, code: str) -> bool:
    """Verifica un código TOTP contra el secreto (con ventana de tolerancia)."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)
