"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, model_validator
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
    celery_broker_url: SecretStr
    extraction_maximum_pages: Annotated[int, Field(gt=0)] = 500
    extraction_maximum_characters: Annotated[int, Field(gt=0)] = 2_000_000
    extraction_lease_seconds: Annotated[int, Field(gt=0)] = 300
    extraction_maximum_attempts: Annotated[int, Field(gt=0)] = 3
    extraction_soft_time_limit_seconds: Annotated[int, Field(gt=0)] = 55
    extraction_hard_time_limit_seconds: Annotated[int, Field(gt=0)] = 60
    outbox_batch_size: Annotated[int, Field(gt=0)] = 100
    outbox_poll_interval_seconds: Annotated[float, Field(gt=0)] = 1.0

    @model_validator(mode="after")
    def validate_time_limits(self) -> "Settings":
        """Require Celery's hard limit to leave room after the soft signal."""
        if self.extraction_hard_time_limit_seconds <= self.extraction_soft_time_limit_seconds:
            raise ValueError("extraction hard time limit must exceed soft time limit")
        return self


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings for the current process."""
    return Settings()  # type: ignore[call-arg]
