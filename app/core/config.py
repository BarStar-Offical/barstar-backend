from __future__ import annotations

from functools import lru_cache
from typing import Any, List, Union

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_nested_delimiter="__",
        extra="ignore",
    )

    environment: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="APP_DEBUG")
    project_name: str = Field(default="Barstar API", alias="APP_NAME")

    backend_host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, alias="BACKEND_PORT")

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    redis_url: RedisDsn = Field(alias="REDIS_URL")

    cors_origins: Union[List[str], str] = Field(default_factory=list, alias="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: Any) -> List[str] | str:
        # Return the string as-is for the validator to process it properly
        # Pydantic will handle the conversion
        if isinstance(value, str) and value:
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            return [str(origin) for origin in value]
        return []


@lru_cache(1)
def get_settings() -> Settings:
    """Return cached settings loaded from the environment."""

    return Settings()  # type: ignore[arg-type]
