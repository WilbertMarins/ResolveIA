"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Infrastructure settings supplied by the execution environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr
    database_health_timeout_seconds: Annotated[float, Field(gt=0)] = 2.0
    object_storage_endpoint_url: str
    object_storage_access_key: SecretStr
    object_storage_secret_key: SecretStr
    object_storage_bucket: str
    object_storage_region: str = "us-east-1"
    object_storage_health_timeout_seconds: Annotated[float, Field(gt=0)] = 2.0
    object_storage_operation_timeout_seconds: Annotated[float, Field(gt=0)] = 10.0


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings for the current process."""
    return Settings()  # type: ignore[call-arg]
