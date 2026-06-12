"""DTOs de autenticación (C-03). Todos rechazan campos extra."""

from pydantic import BaseModel, ConfigDict, Field


class _Schema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LoginRequest(_Schema):
    tenant_slug: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(_Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(_Schema):
    requires_2fa: bool = False
    challenge_token: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshRequest(_Schema):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(_Schema):
    refresh_token: str = Field(min_length=1)


class TwoFactorVerifyRequest(_Schema):
    challenge_token: str = Field(min_length=1)
    code: str = Field(min_length=6, max_length=10)


class TwoFactorConfirmRequest(_Schema):
    code: str = Field(min_length=6, max_length=10)


class Enroll2FAResponse(_Schema):
    secret: str
    provisioning_uri: str


class ForgotPasswordRequest(_Schema):
    tenant_slug: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=320)


class ResetPasswordRequest(_Schema):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=256)


class MessageResponse(_Schema):
    detail: str


class ImpersonateStartRequest(_Schema):
    target_user_id: str = Field(min_length=1)


class ImpersonateAccessResponse(_Schema):
    access_token: str
    token_type: str = "bearer"
    impersonated_id: str | None = None
