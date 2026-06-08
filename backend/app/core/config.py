from functools import lru_cache

from pydantic import Field, field_validator
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
    ENCRYPTION_KEY: str = Field(..., min_length=32, max_length=32, description="AES-256 key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, ge=1)

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
    def validate_encryption_key(cls, v: str) -> str:
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY must be exactly 32 characters")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()