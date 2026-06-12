import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_loads_with_valid_env(settings):
    assert settings.database_url.startswith("postgresql+asyncpg://")
    assert len(settings.secret_key) >= 32
    assert len(settings.encryption_key) == 32


def test_settings_default_access_token_expire_minutes(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://activia:activia@localhost:5432/activia_test",
    )
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    get_settings.cache_clear()

    settings = get_settings()
    assert settings.access_token_expire_minutes == 15


def test_settings_missing_required_variable_fails():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://activia:activia@localhost:5432/activia_test",
            SECRET_KEY="a" * 32,
        )


def test_settings_invalid_type_fails(monkeypatch, expect_settings_validation_error):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://activia:activia@localhost:5432/activia_test",
    )
    monkeypatch.setenv("SECRET_KEY", "a" * 32)
    monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "not-an-integer")

    def build():
        get_settings.cache_clear()
        return get_settings()

    expect_settings_validation_error(build)


def test_settings_short_secret_key_fails(monkeypatch, expect_settings_validation_error):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://activia:activia@localhost:5432/activia_test",
    )
    monkeypatch.setenv("SECRET_KEY", "too-short")
    monkeypatch.setenv("ENCRYPTION_KEY", "b" * 32)

    def build():
        get_settings.cache_clear()
        return get_settings()

    expect_settings_validation_error(build)


def test_settings_invalid_encryption_key_length_fails():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            DATABASE_URL="postgresql+asyncpg://activia:activia@localhost:5432/activia_test",
            SECRET_KEY="a" * 32,
            ENCRYPTION_KEY="not-thirty-two-characters-long",
        )
