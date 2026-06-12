from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    database_url: str = Field(alias="DATABASE_URL")
    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")
    secret_key: str = Field(alias="SECRET_KEY", min_length=32)
    encryption_key: str = Field(alias="ENCRYPTION_KEY")
    access_token_expire_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    two_factor_challenge_expire_minutes: int = Field(
        default=5,
        alias="TWO_FACTOR_CHALLENGE_EXPIRE_MINUTES",
    )
    password_reset_expire_minutes: int = Field(
        default=30,
        alias="PASSWORD_RESET_EXPIRE_MINUTES",
    )
    otel_enabled: bool = Field(default=False, alias="OTEL_ENABLED")
    otel_service_name: str = Field(
        default="activia-trace-api",
        alias="OTEL_SERVICE_NAME",
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @field_validator("encryption_key")
    @classmethod
    def validate_encryption_key(cls, value: str) -> str:
        if len(value) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
