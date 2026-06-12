import base64

import pytest

from app.core.config import Settings
from app.core.security import DecryptionError, decrypt, encrypt


def test_encrypt_decrypt_round_trip(settings: Settings) -> None:
    plaintext = "20-12345678-9"
    assert decrypt(encrypt(plaintext)) == plaintext


def test_ciphertext_differs_from_plaintext(settings: Settings) -> None:
    plaintext = "alumno@activia.test"
    token = encrypt(plaintext)
    assert token != plaintext
    assert plaintext not in token


def test_encrypt_is_non_deterministic(settings: Settings) -> None:
    plaintext = "12345678"
    assert encrypt(plaintext) != encrypt(plaintext)


def test_decrypt_tampered_token_fails(settings: Settings) -> None:
    token = encrypt("secreto")
    raw = bytearray(base64.b64decode(token))
    raw[-1] ^= 0x01  # flip un bit del ciphertext autenticado
    tampered = base64.b64encode(bytes(raw)).decode("ascii")
    with pytest.raises(DecryptionError):
        decrypt(tampered)


def test_decrypt_garbage_fails(settings: Settings) -> None:
    with pytest.raises(DecryptionError):
        decrypt("no-es-base64-valido!!!")


def test_sensitive_value_not_exposed_in_repr() -> None:
    from tests.conftest import SampleEntity

    dni = "20-12345678-9"
    entity = SampleEntity(name="alumno", secret=dni)
    assert dni not in repr(entity)
    assert dni not in str(entity)
