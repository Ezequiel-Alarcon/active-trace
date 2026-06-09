from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
    )

    DATABASE_URL: str = Field(..., description="PostgreSQL connection URL (asyncpg)")
    DATABASE_URL_TEST: str | None = Field(
        default=None,
        description="PostgreSQL connection URL for testing",
    )
    SECRET_KEY: str = Field(..., min_length=32, description="JWT signing key")
    ENCRYPTION_KEY: SecretStr = Field(..., description="AES-256 key (32 bytes)")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 7, ge=1, description="Refresh token lifetime"
    )
    PASSWORD_RESET_TOKEN_TTL_MINUTES: int = Field(
        default=30, ge=1, description="Password recovery token TTL"
    )
    LOGIN_RATE_LIMIT_PER_MINUTE: int = Field(
        default=5, ge=1, description="Max login attempts per window per (ip,email)"
    )
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60, ge=1, description="Sliding window for login rate limit"
    )
    TOTP_ISSUER: str = Field(default="activia-trace", description="TOTP issuer label")
    PASSWORD_MIN_LENGTH: int = Field(default=12, ge=8, description="Minimum password length")

    OTEL_SERVICE_NAME: str = Field(default="activia-trace")
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = Field(default=None)
    OTEL_SDK_ENABLED: bool = Field(default=True)

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    @field_validator("ENCRYPTION_KEY")
    @classmethod
    def validate_encryption_key(cls, v: SecretStr) -> SecretStr:
        raw = v.get_secret_value()
        if len(raw.encode("utf-8")) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 bytes")
        return v

    def key_registry(self) -> dict[int, bytes]:
        raw = self.ENCRYPTION_KEY.get_secret_value().encode("utf-8")
        return {1: raw}

    def current_key_id(self) -> int:
        return 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
