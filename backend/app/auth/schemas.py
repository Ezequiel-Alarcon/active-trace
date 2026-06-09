"""Pydantic v2 DTOs for the auth subsystem (C-03 §3).

All DTOs use `model_config = ConfigDict(extra='forbid')` so unknown fields
are rejected at the boundary.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_codigo: str = Field(..., min_length=1, max_length=64)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=512)
    totp_code: str | None = Field(default=None, min_length=6, max_length=10)


class LoginResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_2fa: bool = False


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=1)


class LogoutResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool = True


class ForgotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_codigo: str = Field(..., min_length=1, max_length=64)
    email: str = Field(..., min_length=1, max_length=255)


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_codigo: str = Field(..., min_length=1, max_length=64)
    selector: str = Field(..., min_length=8, max_length=8)
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=12, max_length=512)


class TwoFactorEnrollResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    otpauth_uri: str
    secret: str


class TwoFactorVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=6, max_length=10)


class TwoFactorVerifyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
