"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Infrastructure settings supplied by the execution environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: SecretStr


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings for the current process."""
    return Settings()  # type: ignore[call-arg]
